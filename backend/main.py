"""
FastAPI 主程序入口。
提供 REST API 和 WebSocket 端点。

重要：ultralytics 的导入有全局副作用，会干扰 FastAPI WebSocket 路由匹配。
因此必须在所有路由注册完毕后再导入 ws.handler（它依赖 ultralytics）。

解耦-B2：REST 路由直接依赖 services/session_service，不再从 ws.handler 导入。
"""

import os
import time
import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket

from config import HOST, PORT, CORS_ORIGINS
from schemas.models import (
    PatientProfile, AcupointDefinitions, ExpertCorrection,
)
from modules.acupoint_estimator import load_acupoint_definitions, compute_correction_factors
from modules.correction_store import get_corrections, save_correction
from services.session_service import (
    get_current_patient, update_patient,
    reload_definitions, get_current_definitions,
)


app = FastAPI(
    title="AI 经络/穴位导航系统 - API",
    version="0.1.0",
    description="基于 YOLOv8-Pose 的穴位识别与导航 MVP",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# WebSocket — 必须在导入 ws.handler 之前注册
# ============================================================

@app.websocket("/ws/realtime")
async def realtime_ws(websocket: WebSocket):
    """实时视频流 + 骨骼识别 + 穴位推算 WebSocket"""
    from ws.handler import ws_handler  # 惰性导入，在首次连接时才触发
    await ws_handler(websocket)


# ============================================================
# 健康检查 — R15 深度监控
# ============================================================

@app.get("/api/health")
async def health_check():
    """深度健康检查 (R15)"""
    health = {
        "status": "ok",
        "version": "0.1.0",
        "timestamp": time.time(),
        "checks": {},
    }

    # 检查 YOLO 模型
    try:
        from modules.pose_estimator import pose_engine
        health["checks"]["yolo_ready"] = pose_engine._yolo is not None
    except Exception as e:
        health["checks"]["yolo_ready"] = False
        health["checks"]["yolo_error"] = str(e)

    # 检查 MediaPipe Hands
    try:
        from modules.pose_estimator import pose_engine
        health["checks"]["mediapipe_ready"] = pose_engine._hand_available
    except Exception as e:
        health["checks"]["mediapipe_ready"] = False
        health["checks"]["mediapipe_error"] = str(e)

    # 检查穴位定义
    try:
        definitions = load_acupoint_definitions()
        health["checks"]["definitions_loaded"] = definitions is not None
        health["checks"]["definitions_count"] = len(definitions.acupoints) if definitions else 0
    except Exception as e:
        health["checks"]["definitions_loaded"] = False
        health["checks"]["definitions_error"] = str(e)

    # 聚合状态
    all_ok = all(
        v for k, v in health["checks"].items()
        if isinstance(v, bool) and not k.endswith("_error")
    )
    health["status"] = "ok" if all_ok else "degraded"

    return health


# ============================================================
# 穴位定义
# ============================================================

@app.get("/api/acupoints/definitions")
async def api_get_acupoint_definitions():
    """获取穴位定义列表"""
    try:
        definitions = load_acupoint_definitions()
        return definitions.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/acupoints/definitions/reload")
async def api_reload_acupoint_definitions():
    """热加载穴位定义文件（通过 session_service，带并发锁）"""
    try:
        await reload_definitions()
        definitions = load_acupoint_definitions()
        return {"status": "ok", "count": len(definitions.acupoints)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# 患者管理 — 直接依赖 session_service
# ============================================================

@app.get("/api/patient/profile")
async def api_get_patient():
    """获取当前患者参数"""
    patient = await get_current_patient()
    return patient.model_dump()


@app.post("/api/patient/profile")
async def api_update_patient(patient: PatientProfile):
    """更新患者参数"""
    await update_patient(patient)
    return {"status": "ok", "patient": patient.model_dump()}


# ============================================================
# 专家修正
# ============================================================

@app.post("/api/expert/correction")
async def api_save_correction(correction: ExpertCorrection):
    """保存专家修正"""
    try:
        saved = save_correction(correction)
        return {"status": "ok", "correction_id": saved.correction_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/expert/corrections")
async def api_get_corrections(patient_id: str = "p_default", acupoint_id: str = None):
    """获取患者的专家修正记录"""
    try:
        corrections = get_corrections(patient_id, acupoint_id)
        return {
            "patient_id": patient_id,
            "count": len(corrections),
            "corrections": [c.model_dump() for c in corrections],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/patient/correction-factors")
async def api_get_correction_factors():
    """获取当前患者的参数修正因子"""
    patient = await get_current_patient()
    factors = compute_correction_factors(patient)
    return factors.model_dump()


# ============================================================
# 启动
# ============================================================

if __name__ == "__main__":
    import asyncio
    config = uvicorn.Config(app, host=HOST, port=PORT, log_level="info")
    server = uvicorn.Server(config)
    asyncio.run(server.serve())
