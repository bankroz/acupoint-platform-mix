"""
共用工具函数模块。

从 acupoint_estimator.py、cun_measurement.py、body_orientation.py、
pose_estimator.py 中提取的重复函数，统一维护。
"""

from typing import Optional
from schemas.models import BodyKeypoint, HandKeypoint, HandLandmarks, PoseResult


def get_keypoint_by_name(result: PoseResult, name: str) -> Optional[BodyKeypoint]:
    """根据名称获取身体关键点 — 归一化坐标 (0~1)"""
    for kp in result.body_keypoints:
        if kp.name == name:
            return kp
    return None


def get_hand_landmark_by_name(hand: HandLandmarks, name: str) -> Optional[HandKeypoint]:
    """根据名称获取手部关键点 — 归一化坐标 (0~1)"""
    for lm in hand.landmarks:
        if lm.name == f"hand_{name}":
            return lm
    return None


def get_hand_by_id(result: PoseResult, hand_id: str) -> Optional[HandLandmarks]:
    """根据 hand_id 获取手部 landmarks"""
    for h in result.hands:
        if h.hand_id == hand_id:
            return h
    return None


# 向后兼容别名（旧代码中使用的 _get_kp）
_get_kp = get_keypoint_by_name
