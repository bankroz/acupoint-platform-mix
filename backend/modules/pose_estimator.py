"""
YOLOv8-Pose + MediaPipe Hands 姿态估计模块。
提供统一的身体关键点和手部关键点检测接口。
后续可替换为其他模型（MMPose/RTMPose），接口保持不变。

适配 mediapipe >= 0.10.14 的 Tasks API。
"""

import os
import time
import cv2
import numpy as np
from typing import Optional

from ultralytics import YOLO
import mediapipe as mp
from mediapipe.tasks import python as mp_tasks
from mediapipe.tasks.python import vision as mp_vision

from config import (
    YOLO_MODEL_NAME, YOLO_CONFIDENCE_THRESHOLD, YOLO_IOU_THRESHOLD,
    MEDIAPIPE_HAND_CONFIDENCE, MEDIAPIPE_HAND_TRACKING_CONFIDENCE,
    FRAME_MAX_WIDTH, BASE_DIR
)
from schemas.models import BodyKeypoint, HandKeypoint, HandLandmarks, PoseResult


# COCO 17 关键点名称（YOLOv8-Pose 输出顺序）
COCO_KEYPOINT_NAMES = [
    "nose",           # 0
    "left_eye",       # 1
    "right_eye",      # 2
    "left_ear",       # 3
    "right_ear",      # 4
    "left_shoulder",  # 5
    "right_shoulder", # 6
    "left_elbow",     # 7
    "right_elbow",    # 8
    "left_wrist",     # 9
    "right_wrist",    # 10
    "left_hip",       # 11
    "right_hip",      # 12
    "left_knee",      # 13
    "right_knee",     # 14
    "left_ankle",     # 15
    "right_ankle",    # 16
]

# MediaPipe Hands 21 关键点名称
HAND_LANDMARK_NAMES = [
    "wrist",              # 0
    "thumb_cmc",          # 1
    "thumb_mcp",          # 2
    "thumb_ip",           # 3
    "thumb_tip",          # 4
    "index_mcp",          # 5
    "index_pip",          # 6
    "index_dip",          # 7
    "index_tip",          # 8
    "middle_mcp",         # 9
    "middle_pip",         # 10
    "middle_dip",         # 11
    "middle_tip",         # 12
    "ring_mcp",           # 13
    "ring_pip",           # 14
    "ring_dip",           # 15
    "ring_tip",           # 16
    "pinky_mcp",          # 17
    "pinky_pip",          # 18
    "pinky_dip",          # 19
    "pinky_tip",          # 20
]

# 模型文件路径（优先使用纯英文路径，避免 MediaPipe C++ 层中文路径兼容问题）
_LOCAL_MODEL = os.path.join(BASE_DIR, "models", "hand_landmarker.task")
_USER_MODEL = os.path.join(os.path.expanduser("~"), ".workbuddy", "models", "hand_landmarker.task")
# 用户目录（纯英文）优先，避免 MediaPipe C++ 读取中文路径失败
HAND_MODEL_PATH = _USER_MODEL if os.path.exists(_USER_MODEL) else _LOCAL_MODEL


class PoseEstimator:
    """姿态估计引擎，封装 YOLOv8-Pose（身体）和 MediaPipe Hands（手部）"""

    def __init__(self):
        self._yolo_model: Optional[YOLO] = None
        self._hand_detector = None
        self._initialized = False
        self._hand_available = False

    def initialize(self):
        """初始化模型（懒加载）"""
        if self._initialized:
            return

        print("[PoseEstimator] 加载 YOLOv8-Pose 模型...")
        self._yolo_model = YOLO(YOLO_MODEL_NAME)
        self._yolo_model.conf = YOLO_CONFIDENCE_THRESHOLD
        self._yolo_model.iou = YOLO_IOU_THRESHOLD
        print(f"[PoseEstimator] YOLOv8-Pose 模型加载完成")

        # 尝试加载 MediaPipe Hands（新版 Tasks API）
        print("[PoseEstimator] 尝试加载 MediaPipe Hands (Tasks API)...")
        try:
            if not os.path.exists(HAND_MODEL_PATH):
                print(f"[PoseEstimator] 手部模型文件不存在: {HAND_MODEL_PATH}")
                print("[PoseEstimator] 手部检测将不可用，身体姿态正常运作")
                self._hand_available = False
            else:
                base_options = mp_tasks.BaseOptions(model_asset_path=HAND_MODEL_PATH)
                options = mp_vision.HandLandmarkerOptions(
                    base_options=base_options,
                    running_mode=mp_vision.RunningMode.IMAGE,
                    num_hands=2,
                    min_hand_detection_confidence=MEDIAPIPE_HAND_CONFIDENCE,
                    min_hand_presence_confidence=MEDIAPIPE_HAND_CONFIDENCE,
                    min_tracking_confidence=MEDIAPIPE_HAND_TRACKING_CONFIDENCE,
                )
                self._hand_detector = mp_vision.HandLandmarker.create_from_options(options)
                self._hand_available = True
                print(f"[PoseEstimator] MediaPipe Hands (Tasks API) 加载完成")
        except Exception as e:
            print(f"[PoseEstimator] 手部模型加载失败: {e}")
            print("[PoseEstimator] 手部检测将不可用，身体姿态正常运作")
            self._hand_available = False

        self._initialized = True
        print("[PoseEstimator] 引擎初始化完成")

    def process_frame(self, frame: np.ndarray) -> PoseResult:
        """
        处理一帧 BGR 图像，返回身体 + 手部关键点。

        Args:
            frame: BGR numpy array (OpenCV 格式)

        Returns:
            PoseResult: 包含身体关键点和手部关键点
        """
        if not self._initialized:
            self.initialize()

        height, width = frame.shape[:2]
        result = PoseResult(
            timestamp=time.time(),
            has_body=False,
            has_hands=False,
        )

        # --- YOLOv8-Pose: 身体关键点 ---
        if self._yolo_model is not None:
            yolo_results = self._yolo_model(frame, verbose=False)

            if yolo_results and len(yolo_results) > 0:
                r = yolo_results[0]
                if r.keypoints is not None and r.keypoints.data is not None and len(r.keypoints.data) > 0:
                    # 取第一个人
                    kps = r.keypoints.data[0]  # shape: (17, 3) -> [x, y, confidence]
                    body_kps = []
                    for i in range(len(kps)):
                        x_val = float(kps[i][0].item())
                        y_val = float(kps[i][1].item())
                        conf = float(kps[i][2].item())
                        body_kps.append(BodyKeypoint(
                            name=COCO_KEYPOINT_NAMES[i] if i < len(COCO_KEYPOINT_NAMES) else f"kp_{i}",
                            x=x_val / width,
                            y=y_val / height,
                            z=None,
                            visibility=conf,
                            confidence=conf,
                        ))
                    result.body_keypoints = body_kps
                    result.has_body = True

                    # 人体边界框
                    if r.boxes is not None and len(r.boxes) > 0:
                        box = r.boxes.xyxy[0]
                        result.body_bbox = {
                            "x": float(box[0].item()),
                            "y": float(box[1].item()),
                            "w": float(box[2].item() - box[0].item()),
                            "h": float(box[3].item() - box[1].item()),
                        }

        # --- MediaPipe Hands (新版 Tasks API): 手部关键点 ---
        hands = []
        if self._hand_available and self._hand_detector is not None:
            try:
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
                mp_result = self._hand_detector.detect(mp_image)

                if mp_result.hand_landmarks and mp_result.handedness:
                    for hand_landmarks, handedness in zip(mp_result.hand_landmarks, mp_result.handedness):
                        # 判断左右手
                        hand_label = handedness[0].category_name  # "Left" or "Right"
                        # MediaPipe 的 "Left" 是摄像头看到的左手 = 实际右手
                        if hand_label == "Left":
                            hand_id = "right_hand"
                        else:
                            hand_id = "left_hand"

                        landmarks = []
                        for i, lm in enumerate(hand_landmarks):
                            landmarks.append(HandKeypoint(
                                name=f"hand_{HAND_LANDMARK_NAMES[i]}",
                                x=lm.x,
                                y=lm.y,
                                z=lm.z,
                                confidence=0.85,
                            ))

                        hands.append(HandLandmarks(
                            hand_id=hand_id,
                            landmarks=landmarks,
                            confidence=0.85,
                        ))
            except Exception as e:
                # 单帧失败不影响整体流程
                pass

        result.hands = hands
        result.has_hands = len(hands) > 0

        return result

    def get_keypoint_by_name(self, result: PoseResult, name: str) -> Optional[BodyKeypoint]:
        """根据名称获取身体关键点"""
        for kp in result.body_keypoints:
            if kp.name == name:
                return kp
        return None

    def get_hand_landmark_by_name(self, hand: HandLandmarks, name: str) -> Optional[HandKeypoint]:
        """根据名称获取手部关键点"""
        for lm in hand.landmarks:
            if lm.name == f"hand_{name}":
                return lm
        return None

    def get_hand_by_id(self, result: PoseResult, hand_id: str) -> Optional[HandLandmarks]:
        """根据手ID获取手部关键点集合"""
        for hand in result.hands:
            if hand.hand_id == hand_id:
                return hand
        return None


# 全局单例
pose_engine = PoseEstimator()
