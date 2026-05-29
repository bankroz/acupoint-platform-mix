"""
同身寸（Cun）计算模块。
支持多种估算方法：身高比例、骨架长度、局部部位比例。
"""

import math
from typing import Optional
from config import CUN_HEIGHT_DIVISOR
from schemas.models import (
    PoseResult, BodyKeypoint, PatientProfile,
    CunEstimate, CunResult, HandLandmarks,
)
from modules.utils import get_keypoint_by_name as _get_kp


def _distance(kp_a: Optional[BodyKeypoint], kp_b: Optional[BodyKeypoint]) -> Optional[float]:
    """计算两个归一化坐标关键点之间的欧氏距离"""
    if kp_a is None or kp_b is None:
        return None
    return math.sqrt((kp_a.x - kp_b.x) ** 2 + (kp_a.y - kp_b.y) ** 2)


def _distance_hand(lm_a, lm_b) -> Optional[float]:
    """计算两个手部关键点之间的欧氏距离"""
    if lm_a is None or lm_b is None:
        return None
    return math.sqrt((lm_a.x - lm_b.x) ** 2 + (lm_a.y - lm_b.y) ** 2)


def estimate_cun(result: PoseResult, patient: Optional[PatientProfile] = None) -> CunResult:
    """
    估算图像中 1 寸等于多少像素（归一化坐标空间）。
    实际 1 寸 ≈ 患者拇指宽度，约身高/75。
    
    估算方法优先级：
    1. 骨架前臂长度 / 12 ≈ 1寸（前臂约12寸）
    2. 腿长度 / 16 ≈ 1寸
    3. 身高估算
    """
    estimates: list[CunEstimate] = []

    # 方法1: 前臂比例 (前臂从肘到腕约12寸)
    for side in ["left", "right"]:
        elbow = _get_kp(result, f"{side}_elbow")
        wrist = _get_kp(result, f"{side}_wrist")
        dist = _distance(elbow, wrist)
        if dist and dist > 0:
            cun = dist / 12.0
            estimates.append(CunEstimate(
                method=f"skeleton_forearm_{side}",
                cun_px=round(cun, 4),
                confidence=0.75,
            ))

    # 方法2: 腿比例 (大腿+小腿约16寸)
    for side in ["left", "right"]:
        hip = _get_kp(result, f"{side}_hip")
        ankle = _get_kp(result, f"{side}_ankle")
        dist = _distance(hip, ankle)
        if dist and dist > 0:
            cun = dist / 16.0
            estimates.append(CunEstimate(
                method=f"skeleton_leg_{side}",
                cun_px=round(cun, 4),
                confidence=0.65,
            ))

    # 方法3: 身高估算
    if patient and patient.height_cm > 0:
        # 1寸 = 身高(cm) / 75 = 图像中的像素比例
        # 简化：假设人体在图像中高度约占 0.7（归一化），则 1寸 ≈ 0.7 / 75
        body_height_ratio = 0.7  # 人体高度约占图像 70%
        cun_height = body_height_ratio / CUN_HEIGHT_DIVISOR
        estimates.append(CunEstimate(
            method="height_based",
            cun_px=round(cun_height, 4),
            confidence=0.5,
        ))

    # 手部局部同身寸（如果有手部关键点）
    if result.hands:
        for hand in result.hands:
            if len(hand.landmarks) >= 21:
                # 同一只手：拇指宽度 ≈ 1寸
                thumb_tip = next((lm for lm in hand.landmarks if lm.name == "hand_thumb_tip"), None)
                thumb_ip = next((lm for lm in hand.landmarks if lm.name == "hand_thumb_ip"), None)
                dist = _distance_hand(thumb_tip, thumb_ip)
                if dist and dist > 0:
                    estimates.append(CunEstimate(
                        method=f"hand_thumb_{hand.hand_id}",
                        cun_px=round(dist * 2.0, 4),  # 拇指关关节到指尖 ≈ 0.5寸
                        confidence=0.6,
                    ))

    # 选择最佳估计（最高置信度）
    if estimates:
        selected = max(estimates, key=lambda e: e.confidence)
    else:
        selected = CunEstimate(
            method="fallback_default",
            cun_px=0.01,  # 默认 1寸 ≈ 1% 图像宽度
            confidence=0.1,
        )

    return CunResult(
        estimates=estimates,
        selected=selected,
    )
