"""
穴位推算引擎。
根据姿态估计结果、穴位定义、同身寸、患者参数，计算穴位在图像中的位置。
"""

import json
import time
import os
from typing import Optional

from config import ACUPOINT_DEFINITION_FILE, MISSING_KEYPOINT_PENALTY
from schemas.models import (
    PoseResult, BodyKeypoint, PatientProfile,
    AcupointDefinition, AcupointDefinitions, AcupointEstimate, AcupointResult,
    BodyOrientation, HandOrientation, CunResult, CorrectionFactors,
    LandmarkRule,
)
from modules.body_orientation import judge_body_orientation
from modules.cun_measurement import estimate_cun
from modules.hand_orientation import judge_hand_orientation


def _get_kp(result: PoseResult, name: str) -> Optional[BodyKeypoint]:
    """获取身体关键点"""
    for kp in result.body_keypoints:
        if kp.name == name:
            return kp
    return None


def _get_hand_lm(hand, name: str):
    """获取手部关键点"""
    if hand is None:
        return None
    for lm in hand.landmarks:
        if lm.name == f"hand_{name}":
            return lm
    return None


def load_acupoint_definitions(filepath: str = ACUPOINT_DEFINITION_FILE) -> AcupointDefinitions:
    """加载穴位定义文件"""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"穴位定义文件不存在: {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    definitions = AcupointDefinitions(**data)
    return definitions


def _compute_acupoint_position(
    acu_def: AcupointDefinition,
    result: PoseResult,
    cun_result: CunResult,
    body_orientation: BodyOrientation,
    hand_orientations: list[HandOrientation],
    patient: Optional[PatientProfile],
    correction_factors: CorrectionFactors,
) -> AcupointEstimate:
    """
    计算单个穴位在图像中的位置。
    """
    warnings: list[str] = []
    confidence: float = 0.5
    x: Optional[float] = None
    y: Optional[float] = None
    source: str = "rule_based"
    orientation_valid: bool = True

    # 检查身体朝向是否匹配
    # 面部/手部/前臂穴位：partial_front 模式也允许（仅上半身/面部可见时）
    is_partial_friendly = acu_def.region in ("face", "head", "hand", "forearm")
    orientation_ok = body_orientation.orientation in acu_def.body_orientations
    if not orientation_ok:
        # partial_front 对面部/手部穴位放行
        if is_partial_friendly and body_orientation.orientation == "partial_front":
            orientation_ok = True
        # 手部穴位无身体朝向要求时也放行
        elif acu_def.requires_hand_keypoints and not acu_def.requires_body_keypoints:
            orientation_ok = True
        else:
            warnings.append(f"身体朝向 {body_orientation.orientation} 不满足穴位要求: {acu_def.body_orientations}")
            orientation_valid = False

    # 检查手部穴位的手掌/手背朝向（放宽：手部已检测到即放行）
    if acu_def.requires_hand_keypoints:
        hand_ok = False
        for ho in hand_orientations:
            if ho.orientation in acu_def.visible_orientations:
                hand_ok = True
                break
        if not hand_ok and acu_def.visible_orientations:
            if len(hand_orientations) == 0:
                warnings.append("未检测到手部，无法定位手部穴位")
                orientation_valid = False
            else:
                # 手部已检测到但朝向不明确 — 允许计算但注记
                warnings.append(f"手部朝向不明确 (检测为: {hand_orientations[0].orientation})，位置仅供参考")

    # 检查所需关键点是否存在
    missing_kps = []
    for kp_name in acu_def.requires_body_keypoints:
        kp = _get_kp(result, kp_name)
        if kp is None or kp.confidence < 0.2:
            missing_kps.append(kp_name)

    if missing_kps:
        warnings.append(f"缺失关键点: {missing_kps}")
        confidence -= MISSING_KEYPOINT_PENALTY * len(missing_kps)

    # 尝试用 landmark_rules 计算位置
    x = None
    y = None
    cun_px = cun_result.selected.cun_px if cun_result.selected else 0.01

    for rule in acu_def.landmark_rules:
        if rule.type == "between_landmarks":
            kp_a = _get_kp(result, rule.landmark_a) if rule.landmark_a else None
            kp_b = _get_kp(result, rule.landmark_b) if rule.landmark_b else None

            # 尝试从手部关键点查找
            if kp_a is None and rule.landmark_a and rule.landmark_a.startswith("hand_"):
                lm_name = rule.landmark_a.replace("hand_", "")
                for hand in result.hands:
                    lm = _get_hand_lm(hand, lm_name)
                    if lm:
                        kp_a = BodyKeypoint(name=rule.landmark_a, x=lm.x, y=lm.y, confidence=lm.confidence)
                        break
            if kp_b is None and rule.landmark_b and rule.landmark_b.startswith("hand_"):
                lm_name = rule.landmark_b.replace("hand_", "")
                for hand in result.hands:
                    lm = _get_hand_lm(hand, lm_name)
                    if lm:
                        kp_b = BodyKeypoint(name=rule.landmark_b, x=lm.x, y=lm.y, confidence=lm.confidence)
                        break

            if kp_a and kp_b and rule.ratio is not None:
                x = kp_a.x + (kp_b.x - kp_a.x) * rule.ratio
                y = kp_a.y + (kp_b.y - kp_a.y) * rule.ratio
                source = f"between_{rule.landmark_a}_{rule.landmark_b}_ratio_{rule.ratio}"
                confidence += 0.2
                break  # 找到第一个有效规则即停止

        elif rule.type == "offset_from_landmark":
            ref_kp = _get_kp(result, rule.reference_landmark) if rule.reference_landmark else None

            # 尝试手部关键点
            if ref_kp is None and rule.reference_landmark and rule.reference_landmark.startswith("hand_"):
                lm_name = rule.reference_landmark.replace("hand_", "")
                for hand in result.hands:
                    lm = _get_hand_lm(hand, lm_name)
                    if lm:
                        ref_kp = BodyKeypoint(name=rule.reference_landmark, x=lm.x, y=lm.y, confidence=lm.confidence)
                        break

            if ref_kp and rule.cun_distance is not None:
                offset = rule.cun_distance * cun_px
                x, y = ref_kp.x, ref_kp.y
                if rule.direction == "up":
                    y -= offset
                elif rule.direction == "down":
                    y += offset
                elif rule.direction == "left":
                    x -= offset
                elif rule.direction == "right":
                    x += offset
                source = f"offset_from_{rule.reference_landmark}_{rule.direction}_{rule.cun_distance}cun"
                confidence += 0.15

    # 如果没算出位置，用兜底
    if x is None or y is None:
        warnings.append("无法根据定义规则计算穴位位置")
        confidence = max(confidence - 0.3, 0.0)

    # 个体参数修正
    if patient and correction_factors:
        confidence -= correction_factors.bmi_confidence_penalty

        if patient.sex == "female":
            for warning in correction_factors.sex_specific_warnings:
                warnings.append(warning)

    confidence = max(min(confidence, 1.0), 0.0)

    # 理疗半径根据置信度调整
    radius_px = acu_def.default_radius_mm / 10.0  # 转换到归一化坐标（简单近似）
    if body_orientation.orientation == "front" or body_orientation.orientation == "back":
        shoulder_width = abs(
            (_get_kp(result, "right_shoulder").x if _get_kp(result, "right_shoulder") else 0.6) -
            (_get_kp(result, "left_shoulder").x if _get_kp(result, "left_shoulder") else 0.4)
        )
        # 肩宽约 40cm，归一化后约 0.2-0.3
        scale = shoulder_width / 0.25 if shoulder_width > 0 else 1.0
        radius_px = (acu_def.default_radius_mm / 400.0) * scale * correction_factors.height_scale
    radius_px = max(radius_px, 0.01)

    visible = orientation_valid and x is not None and y is not None

    return AcupointEstimate(
        id=acu_def.id,
        name_cn=acu_def.name_cn,
        name_en=acu_def.name_en,
        meridian=acu_def.meridian,
        x=x,
        y=y,
        z=None,
        coordinate_type="image_normalized",
        radius_px=round(radius_px, 4),
        confidence=round(confidence, 4),
        source=source,
        orientation_valid=orientation_valid,
        requires_expert_confirm=acu_def.requires_expert_confirm,
        warnings=warnings,
        visible=visible,
    )


def compute_correction_factors(patient: PatientProfile) -> CorrectionFactors:
    """根据患者参数计算修正因子"""
    warnings = []
    sex_warnings = []

    # BMI 修正
    bmi_penalty = 0.0
    if patient.bmi:
        if patient.bmi > 28:
            bmi_penalty = 0.15
            warnings.append(f"BMI[{patient.bmi}]偏高，穴位定位置信度降低{int(bmi_penalty*100)}%")
        elif patient.bmi > 25:
            bmi_penalty = 0.08
            warnings.append(f"BMI[{patient.bmi}]偏高，部分穴位半径增大")

    # 身高修正
    height_scale = 1.0
    if patient.height_cm < 150:
        height_scale = 0.85
    elif patient.height_cm > 190:
        height_scale = 1.15

    # 年龄修正
    age_level = "normal"
    if patient.age > 65:
        age_level = "caution"
        warnings.append("高龄患者，建议降低理疗强度")
    elif patient.age > 80:
        age_level = "high_caution"
        warnings.append("高龄患者，需要严格安全评估")

    # 性别修正
    if patient.sex == "female":
        # 暂不做穴位偏移，仅记录
        pass

    return CorrectionFactors(
        height_scale=round(height_scale, 2),
        bmi_confidence_penalty=round(bmi_penalty, 2),
        age_safety_level=age_level,
        sex_specific_warnings=sex_warnings,
        general_warnings=warnings,
    )


def estimate_acupoints(
    result: PoseResult,
    definitions: AcupointDefinitions,
    patient: Optional[PatientProfile] = None,
    frame_id: str = "",
) -> AcupointResult:
    """
    主入口：根据姿态估计结果推算所有穴位。
    """
    # 朝向判断
    body_orientation = judge_body_orientation(result)

    # 手部朝向
    hand_orientations = []
    for hand in result.hands:
        hand_orientations.append(judge_hand_orientation(hand))

    # 同身寸
    cun_result = estimate_cun(result, patient)

    # 参数修正
    correction_factors = CorrectionFactors()
    if patient:
        correction_factors = compute_correction_factors(patient)

    # 逐个穴位计算
    acupoints = []
    all_warnings = list(correction_factors.general_warnings)

    for acu_def in definitions.acupoints:
        estimate = _compute_acupoint_position(
            acu_def=acu_def,
            result=result,
            cun_result=cun_result,
            body_orientation=body_orientation,
            hand_orientations=hand_orientations,
            patient=patient,
            correction_factors=correction_factors,
        )
        acupoints.append(estimate)
        all_warnings.extend(estimate.warnings)

    return AcupointResult(
        frame_id=frame_id,
        timestamp=time.time(),
        acupoints=acupoints,
        body_orientation=body_orientation,
        hand_orientations=hand_orientations,
        cun_result=cun_result,
        correction_factors=correction_factors.model_dump(),
        warnings=all_warnings,
    )
