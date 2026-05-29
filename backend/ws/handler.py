"""
WebSocket 实时处理模块。
处理前端传来的视频帧，返回姿态估计和穴位推算结果。
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
from schemas.models import (
    PatientProfile, AcupointResult, PoseResult,
    ExpertCorrection, CorrectionFactors,
)
from modules.correction_store import save_correction


# 全局状态（MVP 阶段用内存，后续可换 Redis）
_current_patient: PatientProfile = PatientProfile()
_current_definitions = load_acupoint_definitions()
_expert_corrections: dict[str, dict] = {}  # acupoint_id -> {x, y, radius}


def get_current_patient() -> PatientProfile:
    return _current_patient


def update_patient(patient: PatientProfile):
    global _current_patient
    _current_patient = patient


def reload_definitions():
    global _current_definitions
    _current_definitions = load_acupoint_definitions()


def apply_expert_correction(correction: ExpertCorrection):
    """记录专家修正"""
    global _expert_corrections
    _expert_corrections[correction.acupoint_id] = {
        "x": correction.corrected_position.get("x"),
        "y": correction.corrected_position.get("y"),
        "radius_px": correction.corrected_radius_px,
        "timestamp": correction.timestamp,
    }
    save_correction(correction)


def _decode_frame(data: dict) -> np.ndarray:
    """
    从 WebSocket 消息中解码图像帧。
    支持 base64 JPEG 编码。
    """
    if "image" in data:
        # Base64 JPEG
        img_b64 = data["image"]
        if img_b64.startswith("data:image"):
            img_b64 = img_b64.split(",", 1)[1]
        img_bytes = base64.b64decode(img_b64)
        img_array = np.frombuffer(img_bytes, dtype=np.uint8)
        frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        return frame
    return None


def _encode_response(result: PoseResult, acupoint_result: AcupointResult) -> dict:
    """
    编码 WebSocket 响应为可 JSON 序列化的字典。
    """
    # 应用专家修正
    for acu in acupoint_result.acupoints:
        if acu.id in _expert_corrections:
            corr = _expert_corrections[acu.id]
            acu.expert_corrected_x = corr.get("x")
            acu.expert_corrected_y = corr.get("y")
            acu.expert_corrected = True
            if corr.get("radius_px"):
                acu.radius_px = corr["radius_px"]

    response = {
        "type": "result",
        "timestamp": time.time(),
        "pose": {
            "has_body": result.has_body,
            "has_hands": result.has_hands,
            "body_keypoints": [
                {
                    "name": kp.name,
                    "x": kp.x,
                    "y": kp.y,
                    "confidence": kp.confidence,
                }
                for kp in result.body_keypoints
            ],
            "hands": [
                {
                    "hand_id": h.hand_id,
                    "confidence": h.confidence,
                    "landmarks": [
                        {"name": lm.name, "x": lm.x, "y": lm.y, "confidence": lm.confidence}
                        for lm in h.landmarks
                    ],
                }
                for h in result.hands
            ],
        },
        "acupoint_result": {
            "frame_id": acupoint_result.frame_id,
            "body_orientation": acupoint_result.body_orientation.model_dump() if acupoint_result.body_orientation else None,
            "hand_orientations": [ho.model_dump() for ho in acupoint_result.hand_orientations],
            "cun_result": acupoint_result.cun_result.model_dump() if acupoint_result.cun_result else None,
            "acupoints": [
                {
                    "id": a.id,
                    "name_cn": a.name_cn,
                    "name_en": a.name_en,
                    "meridian": a.meridian,
                    "x": a.x,
                    "y": a.y,
                    "z": a.z,
                    "radius_px": a.radius_px,
                    "confidence": a.confidence,
                    "source": a.source,
                    "orientation_valid": a.orientation_valid,
                    "requires_expert_confirm": a.requires_expert_confirm,
                    "warnings": a.warnings,
                    "visible": a.visible,
                    "expert_corrected_x": a.expert_corrected_x,
                    "expert_corrected_y": a.expert_corrected_y,
                    "expert_corrected": a.expert_corrected,
                }
                for a in acupoint_result.acupoints
            ],
            "correction_factors": acupoint_result.correction_factors,
            "warnings": acupoint_result.warnings,
        },
    }

    return response


async def ws_handler(websocket: WebSocket):
    """WebSocket 连接处理"""
    await websocket.accept()
    print(f"[WS] 客户端已连接")

    # 确保模型已初始化
    pose_engine.initialize()

    frame_count = 0
    try:
        while True:
            # 接收消息
            raw = await websocket.receive_text()
            data = json.loads(raw)
            msg_type = data.get("type", "")

            if msg_type == "frame":
                # 处理帧
                frame = _decode_frame(data)
                if frame is None:
                    await websocket.send_json({"type": "error", "message": "无效的图像数据"})
                    continue

                frame_count += 1

                # 姿态估计
                pose_result = pose_engine.process_frame(frame)

                # 穴位推算
                patient = get_current_patient()
                acu_result = estimate_acupoints(
                    result=pose_result,
                    definitions=_current_definitions,
                    patient=patient,
                    frame_id=f"frame_{frame_count:06d}",
                )

                # 编码并发送结果
                response = _encode_response(pose_result, acu_result)
                await websocket.send_json(response)

            elif msg_type == "patient_update":
                # 更新患者参数
                try:
                    new_patient = PatientProfile(**data.get("data", {}))
                    update_patient(new_patient)
                    await websocket.send_json({
                        "type": "ack",
                        "message": "患者参数已更新",
                        "patient": new_patient.model_dump(),
                    })
                except Exception as e:
                    await websocket.send_json({"type": "error", "message": f"患者参数无效: {e}"})

            elif msg_type == "expert_correction":
                # 专家修正
                try:
                    corr_data = data.get("data", {})
                    correction = ExpertCorrection(**corr_data)
                    apply_expert_correction(correction)
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
        except:
            pass
