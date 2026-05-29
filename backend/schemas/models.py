"""
Pydantic 数据模型定义。
包含患者参数、关键点、朝向判断、同身寸、穴位定义、穴位推算、专家修正、处方、传感器等所有数据结构。
"""
from __future__ import annotations

from typing import Optional, Literal
from pydantic import BaseModel, Field, model_validator


# ============================================================
# 患者参数
# ============================================================

class PatientProfile(BaseModel):
    """患者基本信息"""
    patient_id: str = Field(default="p_default", description="患者ID")
    height_cm: float = Field(default=170.0, ge=50, le=250, description="身高(cm)")
    weight_kg: float = Field(default=65.0, ge=20, le=200, description="体重(kg)")
    age: int = Field(default=35, ge=0, le=150, description="年龄")
    sex: Literal["male", "female", "other"] = Field(default="male", description="性别")
    bmi: Optional[float] = Field(default=None, description="BMI，自动计算")
    body_type: Literal["thin", "normal", "overweight", "obese"] = Field(default="normal", description="体型分类")
    notes: str = Field(default="", description="备注")

    @model_validator(mode='after')
    def compute_bmi_and_type(self) -> 'PatientProfile':
        """Pydantic v2 标准 validator，替代 __init__ 覆写 (解耦-B6)"""
        if self.bmi is None and self.height_cm > 0 and self.weight_kg > 0:
            height_m = self.height_cm / 100.0
            self.bmi = round(self.weight_kg / (height_m ** 2), 1)
        if self.bmi is not None:
            if self.bmi < 18.5:
                self.body_type = "thin"
            elif self.bmi < 25:
                self.body_type = "normal"
            elif self.bmi < 30:
                self.body_type = "overweight"
            else:
                self.body_type = "obese"
        return self


# ============================================================
# 帧数据
# ============================================================

class FrameMeta(BaseModel):
    """帧元数据"""
    camera_id: str = "cam_default"
    camera_type: Literal["rgb", "rgbd", "structured_light"] = "rgb"
    frame_id: str = ""
    timestamp: float = 0.0
    resolution: dict = Field(default_factory=lambda: {"width": 640, "height": 480})
    image_format: str = "rgb"


# ============================================================
# 关键点
# ============================================================

class BodyKeypoint(BaseModel):
    """单个身体关键点"""
    name: str = ""
    x: float = 0.0     # 归一化坐标 [0, 1]
    y: float = 0.0
    z: Optional[float] = None  # 相对深度，MVP 阶段可为 None
    visibility: float = 0.0
    confidence: float = 0.0


class HandKeypoint(BaseModel):
    """单个手部关键点"""
    name: str = ""
    x: float = 0.0
    y: float = 0.0
    z: Optional[float] = None
    confidence: float = 0.0


class HandLandmarks(BaseModel):
    """单只手的关键点集合"""
    hand_id: Literal["left_hand", "right_hand"] = "right_hand"
    landmarks: list[HandKeypoint] = Field(default_factory=list)
    confidence: float = 0.0


class PoseResult(BaseModel):
    """姿态估计结果"""
    pose_model: str = "yolov8n-pose"
    algorithm_version: str = "0.1.0"
    body_keypoints: list[BodyKeypoint] = Field(default_factory=list)
    hands: list[HandLandmarks] = Field(default_factory=list)
    body_bbox: Optional[dict] = None  # {x, y, w, h}
    has_body: bool = False
    has_hands: bool = False


# ============================================================
# 朝向判断
# ============================================================

class BodyOrientation(BaseModel):
    """人体朝向"""
    orientation: Literal["front", "back", "left_side", "right_side", "partial_front", "unknown"] = "unknown"
    confidence: float = 0.0
    reasons: list[str] = Field(default_factory=list)


class HandOrientation(BaseModel):
    """手部朝向"""
    hand_id: str = ""
    orientation: Literal["palm", "back_of_hand", "side", "unknown"] = "unknown"
    confidence: float = 0.0
    reasons: list[str] = Field(default_factory=list)


# ============================================================
# 同身寸
# ============================================================

class CunEstimate(BaseModel):
    """单个同身寸估算方法"""
    method: str = ""
    cun_px: float = 0.0    # 图像中 1 寸等于多少像素
    confidence: float = 0.0


class CunResult(BaseModel):
    """同身寸结果"""
    estimates: list[CunEstimate] = Field(default_factory=list)
    selected: Optional[CunEstimate] = None


# ============================================================
# 穴位定义 (加载自 JSON 文件)
# ============================================================

class LandmarkRule(BaseModel):
    """穴位定位规则"""
    type: str = ""  # "between_landmarks", "offset_from_landmark", "cun_from_landmark"
    landmark_a: Optional[str] = None
    landmark_b: Optional[str] = None
    ratio: Optional[float] = None       # 两点间的比例位置
    reference_landmark: Optional[str] = None
    direction: Optional[str] = None      # "left", "right", "up", "down"
    cun_distance: Optional[float] = None  # 偏离参考点多少寸
    description: str = ""


class AcupointDefinition(BaseModel):
    """穴位定义"""
    id: str = ""
    name_cn: str = ""
    name_en: str = ""
    meridian: str = ""
    body_side: str = "left_or_right"
    visible_orientations: list[str] = Field(default_factory=list)  # ["palm", "back_of_hand"]
    body_orientations: list[str] = Field(default_factory=list)     # ["front", "back"]
    region: str = ""  # "head", "neck", "shoulder", "hand", "leg", "back"
    definition_method: str = ""
    landmark_rules: list[LandmarkRule] = Field(default_factory=list)
    cun_rules: list[dict] = Field(default_factory=list)
    requires_hand_keypoints: bool = False
    requires_body_keypoints: list[str] = Field(default_factory=list)
    default_radius_mm: float = 10.0
    safety_level: Literal["low", "medium", "high"] = "low"
    requires_expert_confirm: bool = True
    contraindications: list[str] = Field(default_factory=list)


class AcupointDefinitions(BaseModel):
    """穴位定义集合"""
    version: str = "0.1.0"
    source: str = "rule_based_definition"
    coordinate_system: str = "relative_body_landmark"
    acupoints: list[AcupointDefinition] = Field(default_factory=list)


# ============================================================
# 穴位推算结果
# ============================================================

class AcupointEstimate(BaseModel):
    """单个穴位推算结果"""
    id: str = ""
    name_cn: str = ""
    name_en: str = ""
    meridian: str = ""
    x: Optional[float] = None
    y: Optional[float] = None
    z: Optional[float] = None
    coordinate_type: str = "image_normalized"
    radius_px: float = 12.0
    confidence: float = 0.0
    source: str = ""
    orientation_valid: bool = True
    requires_expert_confirm: bool = True
    warnings: list[str] = Field(default_factory=list)
    visible: bool = True
    # 专家修正后的位置 (如果有)
    expert_corrected_x: Optional[float] = None
    expert_corrected_y: Optional[float] = None
    expert_corrected: bool = False


class AcupointResult(BaseModel):
    """一帧的穴位推算结果"""
    frame_id: str = ""
    timestamp: float = 0.0
    acupoints: list[AcupointEstimate] = Field(default_factory=list)
    body_orientation: Optional[BodyOrientation] = None
    hand_orientations: list[HandOrientation] = Field(default_factory=list)
    cun_result: Optional[CunResult] = None
    correction_factors: dict = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


# ============================================================
# 专家修正
# ============================================================

class ExpertCorrection(BaseModel):
    """专家修正记录"""
    correction_id: str = ""
    timestamp: float = 0.0
    expert_id: str = "expert_default"
    patient_id: str = ""
    frame_id: str = ""
    acupoint_id: str = ""
    ai_position: dict = Field(default_factory=dict)        # {x, y, z}
    corrected_position: dict = Field(default_factory=dict)  # {x, y, z}
    corrected_radius_px: Optional[float] = None
    correction_distance_px: float = 0.0
    correction_reasons: list[str] = Field(default_factory=list)
    expert_confidence: float = 0.9
    notes: str = ""
    algorithm_version: str = "0.1.0"
    acupoint_definition_version: str = "0.1.0"


# ============================================================
# 诊疗处方
# ============================================================

class TherapyStep(BaseModel):
    """理疗步骤"""
    step: int = 0
    region: str = ""
    acupoint_ids: list[str] = Field(default_factory=list)
    device: str = ""
    duration_sec: int = 0
    intensity: str = ""
    notes: str = ""


class Prescription(BaseModel):
    """诊疗处方"""
    prescription_id: str = ""
    patient_id: str = ""
    diagnosis: str = ""
    target_regions: list[str] = Field(default_factory=list)
    recommended_acupoints: list[str] = Field(default_factory=list)
    therapy_plan: list[TherapyStep] = Field(default_factory=list)
    contraindications: list[str] = Field(default_factory=list)
    created_by: str = ""
    warnings: list[str] = Field(default_factory=list)


# ============================================================
# 传感器数据
# ============================================================

class SensorData(BaseModel):
    """传感器数据"""
    sensor_id: str = ""
    device_id: str = ""
    frame_id: str = ""
    timestamp: float = 0.0
    sensor_type: str = ""   # "pressure", "temperature", "vibration", "heart_rate"
    value: float = 0.0
    unit: str = ""
    status: str = "normal"


class SensorSnapshot(BaseModel):
    """一帧传感器快照"""
    frame_id: str = ""
    timestamp: float = 0.0
    readings: list[SensorData] = Field(default_factory=list)


# ============================================================
# WebSocket 消息类型
# ============================================================

class WSMessage(BaseModel):
    """WebSocket 通信消息"""
    type: str = ""  # "frame", "result", "patient_update", "expert_correction", "error"
    data: dict = Field(default_factory=dict)


# ============================================================
# 人体修正因子
# ============================================================

class CorrectionFactors(BaseModel):
    """个体参数修正因子"""
    height_scale: float = 1.0
    bmi_confidence_penalty: float = 0.0
    age_safety_level: Literal["normal", "caution", "high_caution"] = "normal"
    sex_specific_warnings: list[str] = Field(default_factory=list)
    general_warnings: list[str] = Field(default_factory=list)
