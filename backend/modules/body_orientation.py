"""
人体正反面/侧面判断模块。
基于 YOLOv8-Pose 关键点的可见性和空间关系判断人体朝向。
"""

from typing import Optional, Literal
from config import FRONT_NOSE_CONFIDENCE_MIN, SIDE_SHOULDER_RATIO_MAX
from schemas.models import (
    PoseResult, BodyOrientation, BodyKeypoint
)


def _get_kp(result: PoseResult, name: str) -> Optional[BodyKeypoint]:
    """快捷获取关键点"""
    for kp in result.body_keypoints:
        if kp.name == name:
            return kp
    return None


def judge_body_orientation(result: PoseResult) -> BodyOrientation:
    """
    判断人体当前朝向：front / back / left_side / right_side / unknown。
    
    算法：
    - 鼻子、眼睛可见 + 左右肩宽度正常 → front
    - 鼻子不可见 + 肩/髋可见 → back
    - 左右肩水平距离显著压缩 → side（根据肩X轴位置判断左右）
    - 以上都不满足 → unknown
    """
    reasons: list[str] = []
    
    # 获取关键点
    nose = _get_kp(result, "nose")
    left_eye = _get_kp(result, "left_eye")
    right_eye = _get_kp(result, "right_eye")
    left_ear = _get_kp(result, "left_ear")
    right_ear = _get_kp(result, "right_ear")
    left_shoulder = _get_kp(result, "left_shoulder")
    right_shoulder = _get_kp(result, "right_shoulder")
    left_hip = _get_kp(result, "left_hip")
    right_hip = _get_kp(result, "right_hip")

    # 检查是否有足够关键点
    shoulder_available = left_shoulder is not None and right_shoulder is not None
    hip_available = left_hip is not None and right_hip is not None

    if not shoulder_available:
        # 检查是否至少面部可见 → 判定为 partial_front
        face_visible = (
            nose is not None and nose.confidence > FRONT_NOSE_CONFIDENCE_MIN
        ) or (
            left_eye is not None and left_eye.confidence > FRONT_NOSE_CONFIDENCE_MIN
        )
        if face_visible:
            face_conf = nose.confidence if nose else (left_eye.confidence if left_eye else 0.5)
            return BodyOrientation(
                orientation="partial_front",
                confidence=face_conf * 0.8,
                reasons=["face_visible_shoulders_not_detected"],
            )
        return BodyOrientation(
            orientation="unknown",
            confidence=0.0,
            reasons=["shoulder_keypoints_missing"],
        )

    # === 正面判断 ===
    # 鼻子置信度高 + 眼睛/耳朵可见 → 正面
    face_visible = False
    face_confidence = 0.0

    if nose is not None and nose.confidence > FRONT_NOSE_CONFIDENCE_MIN:
        face_visible = True
        face_confidence = nose.confidence
        reasons.append("face_keypoints_visible")

    if left_eye is not None and left_eye.confidence > FRONT_NOSE_CONFIDENCE_MIN:
        face_visible = True
        face_confidence = max(face_confidence, left_eye.confidence)
        reasons.append("eyes_visible")

    # 肩宽检查
    shoulder_width = abs(right_shoulder.x - left_shoulder.x)
    
    if hip_available:
        hip_width = abs(right_hip.x - left_hip.x)
        body_width_ref = max(shoulder_width, hip_width)
    else:
        body_width_ref = shoulder_width
    
    # 左右肩顺序确认（X轴：左 < 右 表正面/背面，左 > 右 表背面摄像头视角）
    shoulder_order_correct = left_shoulder.x < right_shoulder.x
    shoulder_asymmetry = abs(shoulder_width / max(body_width_ref, 0.001))

    if face_visible and shoulder_order_correct and shoulder_asymmetry > SIDE_SHOULDER_RATIO_MAX:
        reasons.append("shoulder_width_normal")
        reasons.append("left_right_shoulder_order_consistent")
        conf = 0.7 + face_confidence * 0.3
        return BodyOrientation(
            orientation="front",
            confidence=min(conf, 1.0),
            reasons=reasons,
        )

    # === 侧面判断 ===
    if shoulder_asymmetry <= SIDE_SHOULDER_RATIO_MAX:
        reasons.append("shoulder_width_compressed")
        # 根据鼻子位置判断左/右侧面
        if nose is not None and nose.x < left_shoulder.x:
            reasons.append("nose_on_left_side")
            return BodyOrientation(
                orientation="left_side",
                confidence=0.6,
                reasons=reasons,
            )
        elif nose is not None and nose.x > right_shoulder.x:
            reasons.append("nose_on_right_side")
            return BodyOrientation(
                orientation="right_side",
                confidence=0.6,
                reasons=reasons,
            )
        else:
            # 无法确定左右，判断为侧面
            return BodyOrientation(
                orientation="right_side",  # 默认右，置信度低
                confidence=0.4,
                reasons=reasons,
            )

    # === 背面判断 ===
    # 鼻子不可见 + 肩髋可见 → 背面
    face_absent = (nose is None or nose.confidence < FRONT_NOSE_CONFIDENCE_MIN) and \
                  (left_eye is None or left_eye.confidence < FRONT_NOSE_CONFIDENCE_MIN)
    
    if face_absent and shoulder_available:
        reasons.append("face_keypoints_not_visible")
        reasons.append("shoulder_hip_detected")
        conf = 0.5
        
        if hip_available:
            conf += 0.15
            reasons.append("hip_confirmed")
        
        return BodyOrientation(
            orientation="back",
            confidence=min(conf, 1.0),
            reasons=reasons,
        )

    # === 无法判断 ===
    reasons.append("insufficient_information")
    return BodyOrientation(
        orientation="unknown",
        confidence=0.2,
        reasons=reasons,
    )
