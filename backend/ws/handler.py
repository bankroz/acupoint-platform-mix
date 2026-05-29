"""
WebSocket 实时处理模块。
处理前端传来的视频帧，返回姿态估计和穴位推算结果。

解耦-B2：会话状态管理已迁移到 services/session_service.py。
解耦-B4：_encode_response 使用 model.model_dump() 替代手工序列化。
B2：帧背压控制（is_processing 锁 + 超时保护）。
"""

import asyncio
import base64
import cv2
import json
import numpy as np
import time

from fastapi import WebSocket, WebSocketDisconnect

from modules.pose_estimator import pose_engine
from modules.acupoint_estimator import (
    load_acupoint_definitions, estimate_acupoints,
    compute_correction_factors,
)
from modules.correction_store import save_correction
from services.session_service import (
    get_current_patient, update_patient,
    get_current_definitions, reload_definitions,
    apply_expert_correction, get_expert_corrections,
)

from schemas.models import (
    PatientProfile, PoseResult, AcupointResult,
    ExpertCorrection,
)

# ============================================================
# 帧背压控制 (B2)
# ============================================================

_is_processing = False
FRAME_PROCESSING_TIMEOUT = 1.0  # 秒

# ============================================================
# 帧编解码
# ============================================================

def _decode_frame(data: dict) -> np.ndarray | None:
    """
    从 WebSocket 消息中解码图像帧。
    支持 base64 JPEG 编码。含注入攻击防护 (R11)。
    """
    if "image" not in data:
        return None

    img_b64 = data["image"]
    if isinstance(img_b64, str) and img_b64.startswith("data:image"):
        img_b64 = img_b64.split(",", 1)[1]

    # 大小限制：2MB base64 上限
    if len(img_b64) > 2 * 1024 * 1024:
        print("[WS] 帧过大，丢弃")
        return None

    try:
        img_bytes = base64.b64decode(img_b64)
    except Exception:
        return None

    # 文件头魔数校验
    if not (img_bytes[:2] == b'\xff\xd8' or img_bytes[:4] == b'\x89PNG'):
        return None

    img_array = np.frombuffer(img_bytes, dtype=np.uint8)
    return cv2.imdecode(img_array, cv2.IMREAD_COLOR)


async def _process_single_frame(frame, frame_count: int, session_id: str | None = None):
    """
    单帧处理管道（可被 asyncio.wait_for 超时）。
    将同步处理包装为 async，以便超时控制。
    """
    loop = asyncio.get_running_loop()

    # 姿态估计（CPU 密集型，在线程池中运行）
    pose_result = await loop.run_in_executor(None, pose_engine.process_frame, frame)

    # 穴位推算（规则驱动，轻量）
    patient = await get_current_patient(session_id)
    definitions = await get_current_definitions(session_id)
    acu_result = estimate_acupoints(
        result=pose_result,
        definitions=definitions,
        patient=patient,
        frame_id=f"frame_{frame_count:06d}",
    )

    return pose_result, acu_result


def _encode_response(result: PoseResult, acupoint_result: AcupointResult) -> dict:
    """
    编码 WebSocket 响应 (解耦-B4: 使用 model_dump 替代手工序列化)。
    """
    # 先序列化，再注入专家修正
    acu_dict = acupoint_result.model_dump()

    # 应用内存中的专家修正（由 ws_handler 注入）
    # 注意：修正数据在 ws_handler 中通过 session_service 获取

    response = {
        "type": "result",
        "timestamp": time.time(),
        "pose": {
            "has_body": result.has_body,
            "has_hands": result.has_hands,
            "body_keypoints": [kp.model_dump() for kp in result.body_keypoints],
            "hands": [h.model_dump() for h in result.hands],
        },
        "acupoint_result": acu_dict,
    }

    return response


# ============================================================
# WebSocket Handler
# ============================================================

async def ws_handler(websocket: WebSocket):
    """WebSocket 连接处理 — 带帧背压控制 (B2) 和会话隔离"""
    global _is_processing

    await websocket.accept()
    session_id = websocket.query_params.get("session_id")
    print(f"[WS] 客户端已连接 (session={session_id or '默认'})")

    # 确保模型已初始化
    pose_engine.initialize()

    frame_count = 0
    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            msg_type = data.get("type", "")

            if msg_type == "frame":
                # 背压控制：正在处理上一帧时跳过
                if _is_processing:
                    await websocket.send_json({"type": "skip", "message": "服务端繁忙，帧已跳过"})
                    continue

                frame = _decode_frame(data)
                if frame is None:
                    await websocket.send_json({"type": "error", "message": "无效的图像数据"})
                    continue

                frame_count += 1
                _is_processing = True

                try:
                    pose_result, acu_result = await asyncio.wait_for(
                        _process_single_frame(frame, frame_count, session_id),
                        timeout=FRAME_PROCESSING_TIMEOUT,
                    )

                    # 注入专家修正
                    corrections = await get_expert_corrections(session_id)
                    for acu in acu_result.acupoints:
                        if acu.id in corrections:
                            corr = corrections[acu.id]
                            acu.expert_corrected_x = corr.get("x")
                            acu.expert_corrected_y = corr.get("y")
                            acu.expert_corrected = True
                            if corr.get("radius_px"):
                                acu.radius_px = corr["radius_px"]

                    response = _encode_response(pose_result, acu_result)
                    await websocket.send_json(response)

                except asyncio.TimeoutError:
                    print(f"[WS] 帧 {frame_count} 处理超时 ({FRAME_PROCESSING_TIMEOUT}s)")
                    await websocket.send_json({
                        "type": "timeout",
                        "message": f"帧处理超时 ({FRAME_PROCESSING_TIMEOUT}s)",
                        "frame_id": f"frame_{frame_count:06d}",
                    })
                finally:
                    _is_processing = False

            elif msg_type == "patient_update":
                try:
                    new_patient = PatientProfile(**data.get("data", {}))
                    await update_patient(new_patient, session_id)
                    await websocket.send_json({
                        "type": "ack",
                        "message": "患者参数已更新",
                        "patient": new_patient.model_dump(),
                    })
                except Exception as e:
                    await websocket.send_json({"type": "error", "message": f"患者参数无效: {e}"})

            elif msg_type == "expert_correction":
                try:
                    corr_data = data.get("data", {})
                    correction = ExpertCorrection(**corr_data)
                    await apply_expert_correction(correction, session_id)
                    await websocket.send_json({
                        "type": "ack",
                        "message": f"穴位 {correction.acupoint_id} 已修正",
                        "correction_id": correction.correction_id,
                    })
                except Exception as e:
                    await websocket.send_json({"type": "error", "message": f"修正数据无效: {e}"})

            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})

            else:
                await websocket.send_json({"type": "error", "message": f"未知消息类型: {msg_type}"})

    except WebSocketDisconnect:
        print(f"[WS] 客户端断开，共处理 {frame_count} 帧")
    except Exception as e:
        print(f"[WS] 异常: {e}")
        try:
            await websocket.close()
        except Exception:
            pass
