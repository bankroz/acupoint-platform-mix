"""
FastAPI 主程序入口。
提供 REST API 和 WebSocket 端点。

重要：ultralytics 的导入有全局副作用，会干扰 FastAPI WebSocket 路由匹配。
因此必须在所有路由注册完毕后再导入 ws.handler（它依赖 ultralytics）。
"""

import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from config import HOST, PORT, CORS_ORIGINS
from schemas.models import (
    PatientProfile, AcupointDefinitions, ExpertCorrection,
)
from modules.acupoint_estimator import load_acupoint_definitions, compute_correction_factors
from modules.correction_store import get_corrections, save_correction


app = FastAPI(
    title="AI 经络/穴位导航系统 - API",
    version="0.1.0",
    description="基于 YOLOv8-Pose 的穴位识别与导航 MVP",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# WebSocket — 必须在导入 ws.handler 之前注册
# （使用惰性导入避免 ultralytics 干扰路由匹配）
# ============================================================

@app.websocket("/ws/realtime")
async def realtime_ws(websocket: WebSocket):
    """实时视频流 + 骨骼识别 + 穴位推算 WebSocket"""
    from ws.handler import ws_handler  # 惰性导入，在首次连接时才触发
    await ws_handler(websocket)


# ============================================================
# 健康检查 — 不依赖 ws.handler
# ============================================================

@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {
        "status": "ok",
        "version": "0.1.0",
        "modules": {
            "pose_estimation": "yolov8n-pose + mediapipe_hands",
            "acupoint_definitions": "acupoints_v0.1.json",
        }
    }


# ============================================================
# 穴位定义（不依赖 ws.handler 状态）
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
    """热加载穴位定义文件"""
    from ws.handler import reload_definitions
    try:
        reload_definitions()
        definitions = load_acupoint_definitions()
        return {"status": "ok", "count": len(definitions.acupoints)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# 以下路由依赖 ws.handler 的状态管理函数
# 必须等 ws.handler 导入后才能在运行时正确引用
# ============================================================

@app.get("/api/patient/profile")
async def api_get_patient():
    """获取当前患者参数"""
    from ws.handler import get_current_patient
    return get_current_patient().model_dump()


@app.post("/api/patient/profile")
async def api_update_patient(patient: PatientProfile):
    """更新患者参数"""
    from ws.handler import update_patient
    update_patient(patient)
    return {"status": "ok", "patient": patient.model_dump()}


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
    from ws.handler import get_current_patient
    patient = get_current_patient()
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
