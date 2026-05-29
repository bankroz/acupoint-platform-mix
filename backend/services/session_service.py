"""
会话状态管理服务 — 独立于 WebSocket 层。

解耦-B2：从 ws/handler.py 提取全局状态管理逻辑，
REST API 不再依赖 WS handler 导入，实现通信层与业务逻辑层解耦。

每个 WebSocket 连接绑定独立 session_id，解决 B1 会话并发隔离问题。
"""

import asyncio
import time
import uuid
from typing import Optional

from schemas.models import (
    PatientProfile, AcupointDefinitions, ExpertCorrection,
)
from modules.acupoint_estimator import load_acupoint_definitions
from modules.correction_store import save_correction


# ============================================================
# Session 数据类 — B1 会话并发隔离
# ============================================================

class SessionContext:
    """单次会话的隔离上下文"""
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.patient: PatientProfile = PatientProfile()
        self.definitions: AcupointDefinitions = load_acupoint_definitions()
        self.expert_corrections: dict[str, dict] = {}
        self.created_at: float = time.time()
        self.last_active: float = time.time()

    def touch(self):
        self.last_active = time.time()


# ============================================================
# 全局会话注册表
# ============================================================

_sessions: dict[str, SessionContext] = {}
_sessions_lock = asyncio.Lock()
SESSION_TTL_SECONDS = 300  # 5 分钟无活动自动清理

# 兼容旧代码的「默认会话」（MVP 阶段单用户场景向后兼容）
_default_session: Optional[SessionContext] = None


async def create_session() -> SessionContext:
    """创建新会话，返回 session_context"""
    async with _sessions_lock:
        session_id = uuid.uuid4().hex[:12]
        ctx = SessionContext(session_id)
        _sessions[session_id] = ctx
        return ctx


async def get_session(session_id: str) -> Optional[SessionContext]:
    """根据 session_id 获取会话上下文"""
    async with _sessions_lock:
        ctx = _sessions.get(session_id)
        if ctx:
            ctx.touch()
        return ctx


async def destroy_session(session_id: str):
    """销毁会话"""
    async with _sessions_lock:
        _sessions.pop(session_id, None)


async def _gc_expired_sessions():
    """清理过期会话"""
    now = time.time()
    async with _sessions_lock:
        expired = [
            sid for sid, ctx in _sessions.items()
            if now - ctx.last_active > SESSION_TTL_SECONDS
        ]
        for sid in expired:
            _sessions.pop(sid, None)
    if expired:
        print(f"[Session] 清理 {len(expired)} 个过期会话")


# ============================================================
# 兼容旧代码的全局状态 API（默认会话模式）
# ============================================================

async def _ensure_default_session() -> SessionContext:
    """确保默认会话存在"""
    global _default_session
    if _default_session is None:
        _default_session = await create_session()
    return _default_session


# ---- 患者管理 ----

async def get_current_patient(session_id: Optional[str] = None) -> PatientProfile:
    """获取当前患者参数"""
    if session_id:
        ctx = await get_session(session_id)
        if ctx:
            return ctx.patient
    ctx = await _ensure_default_session()
    return ctx.patient


async def update_patient(patient: PatientProfile, session_id: Optional[str] = None):
    """更新患者参数"""
    if session_id:
        ctx = await get_session(session_id)
        if ctx:
            ctx.patient = patient
            return
    ctx = await _ensure_default_session()
    ctx.patient = patient


# ---- 穴位定义管理 ----

async def get_current_definitions(session_id: Optional[str] = None) -> AcupointDefinitions:
    """获取当前穴位定义"""
    if session_id:
        ctx = await get_session(session_id)
        if ctx:
            return ctx.definitions
    ctx = await _ensure_default_session()
    return ctx.definitions


# 热加载锁 (B5/B8)
_definition_lock = asyncio.Lock()


async def reload_definitions(session_id: Optional[str] = None):
    """热加载穴位定义（带读写锁，保证并发安全）"""
    async with _definition_lock:
        new_defs = load_acupoint_definitions()
        if session_id:
            ctx = await get_session(session_id)
            if ctx:
                ctx.definitions = new_defs
                return
        ctx = await _ensure_default_session()
        ctx.definitions = new_defs


# ---- 专家修正 ----

async def apply_expert_correction(correction: ExpertCorrection, session_id: Optional[str] = None):
    """记录专家修正"""
    ctx = await _ensure_default_session() if not session_id else await get_session(session_id)
    if ctx is None:
        ctx = await _ensure_default_session()

    ctx.expert_corrections[correction.acupoint_id] = {
        "x": correction.corrected_position.get("x"),
        "y": correction.corrected_position.get("y"),
        "radius_px": correction.corrected_radius_px,
        "timestamp": correction.timestamp,
    }
    save_correction(correction)


async def get_expert_corrections(session_id: Optional[str] = None) -> dict[str, dict]:
    """获取当前会话的专家修正"""
    ctx = await _ensure_default_session() if not session_id else await get_session(session_id)
    if ctx is None:
        ctx = await _ensure_default_session()
    return ctx.expert_corrections
