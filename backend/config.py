"""
系统集中配置文件。
所有路径、模型参数、阈值集中在此，禁止在其他模块硬编码。
"""

import os

# === 项目根路径 ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

# === 数据路径 ===
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
ACUPOINT_DEFINITIONS_DIR = os.path.join(DATA_DIR, "acupoint_definitions")
ACUPOINT_DEFINITION_FILE = os.path.join(ACUPOINT_DEFINITIONS_DIR, "acupoints_v0.1.json")
SESSIONS_DIR = os.path.join(PROJECT_ROOT, "sessions")
CORRECTIONS_DIR = os.path.join(PROJECT_ROOT, "corrections")

# === 模型配置 ===
YOLO_MODEL_NAME = "yolov8n-pose.pt"  # 使用最小模型，快速启动
YOLO_CONFIDENCE_THRESHOLD = 0.5
YOLO_IOU_THRESHOLD = 0.45

# MediaPipe Hands
MEDIAPIPE_HAND_CONFIDENCE = 0.5
MEDIAPIPE_HAND_TRACKING_CONFIDENCE = 0.5

# === 图像处理配置 ===
FRAME_MAX_WIDTH = 640
FRAME_JPEG_QUALITY = 70

# === WebSocket 配置 ===
WS_FRAME_INTERVAL_MS = 150  # 前端发送帧间隔

# === 同身寸配置 (Cun Measurement) ===
# 默认一寸 = 身高 / 75 (近似值)
CUN_HEIGHT_DIVISOR = 75

# 不同区域的局部同身寸参考
# 拇指宽度 ≈ 1 寸，四指并拢宽度 ≈ 3 寸
CUN_LOCAL_REFERENCE = {
    "thumb_breadth_cm": 2.0,    # 拇指宽度约 2cm
    "four_fingers_cm": 6.0,     # 四指并拢约 6cm
}

# === 穴位推算阈值 ===
# 正面需要鼻子置信度
FRONT_NOSE_CONFIDENCE_MIN = 0.3
# 侧面判断：左右肩 X 轴比例阈值
SIDE_SHOULDER_RATIO_MAX = 0.3  # 左右肩距离 / 人体宽度 < 此值 → 侧面
# 关键点缺失时的默认置信度惩罚
MISSING_KEYPOINT_PENALTY = 0.3

# === 服务器配置 ===
HOST = "0.0.0.0"
PORT = 8765
CORS_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:5176",
    "http://localhost:5174",
    "http://localhost:5175",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5176",
    "null",  # 本地文件访问
]  # MVP 阶段放宽，WebSocket 需显式列出 origin

# === 确保必要目录存在 ===
for d in [SESSIONS_DIR, CORRECTIONS_DIR]:
    os.makedirs(d, exist_ok=True)
