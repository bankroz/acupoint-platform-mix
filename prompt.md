# Agent 开发任务 Prompt：AI 经络/穴位导航理疗系统 MVP 架构设计与初始开发

你是一个资深 AI 视觉算法 + Web 全栈 + 医疗/康复设备原型系统架构 Agent。

请为我设计并初步实现一个 **AI 经络/穴位导航理疗系统 MVP**。

该系统的第一阶段目标不是自动针灸，也不是机械臂控制，而是：

> 基于普通 RGB 相机，快速验证人体骨架识别、人体正反面判断、手掌/手背判断、同身寸穴位推算、穴位标注文件加载、专家修正、实时浏览器可视化的整体技术链路。

系统应支持后续升级到：

- 多 RGB 相机；
- RGB-D 相机；
- 结构光相机；
- 深度数据修正穴位；
- 投影/振镜导航；
- 标准化理疗终端；
- 压力/温度/震动等传感器；
- 患者诊疗处方数据；
- 专家纠偏数据集；
- 未来机械臂/自动执行接口。

当前请优先构建 **MVP 架构 + 可运行 Demo**，不要求医疗级精度，但要求模块边界清晰、数据结构可扩展、后续可替换算法模型。

---

# 一、产品目标

开发一个浏览器界面系统，实现：

1. 打开摄像头或读取视频流；
2. 实时识别人体骨架关键点；
3. 判断人体当前是正面、背面、侧面或不确定；
4. 判断手部区域是手掌、手背或不确定；
5. 根据人体骨架关键点和用户基本参数，推算若干穴位位置；
6. 支持从单独穴位标注文件中加载穴位定义；
7. 支持基于“同身寸”规则推算穴位；
8. 支持输入身高、体重、年龄、性别等信息，并用于穴位位置修正；
9. 支持专家在浏览器界面中拖动/点击修正穴位位置；
10. 记录 AI 原始穴位点、专家修正点、修正原因和置信度；
11. 实时在浏览器画面中叠加显示：
    - 摄像头画面；
    - 骨架关键点；
    - 穴位点；
    - 穴位名称；
    - 置信度；
    - 经络线；
    - 专家修正点；
    - 患者参数；
    - 诊疗处方；
    - 传感器数据；
12. 预留多相机、结构光相机和深度数据接口，用于未来三维修正。

---

# 二、技术路线原则

## 1. 第一阶段优先 RGB 相机

当前 MVP 优先使用普通 RGB 摄像头，目标是快速验证：

- 单目图像下人体关键点识别是否稳定；
- 骨架关键点能否支持粗略穴位定位；
- 正反面判断是否可行；
- 同身寸穴位推算是否能形成初步视觉效果；
- 专家修正流程是否顺畅；
- 浏览器端实时显示是否可用。

不要第一阶段就依赖结构光相机、深度相机或复杂机械结构。

---

## 2. 穴位不要建模为绝对医学点

第一阶段穴位输出应建模为：

```text
推荐中心点
+
推荐作用区域半径
+
置信度
+
来源说明
+
是否需要专家确认
```

不要把穴位表现为绝对精确点。  
应显示为一个带半径的圆形/椭圆区域，并允许专家修正。

---

## 3. 算法应采用“骨架关键点 + 中医规则 + 参数修正 + 专家纠偏”的混合路线

不要只做纯深度学习黑箱。

推荐初始路线：

```text
RGB 图像
    ↓
人体检测/姿态估计
    ↓
骨架关键点
    ↓
人体朝向判断
    ↓
身体部位比例估算
    ↓
同身寸规则推算
    ↓
穴位标注文件加载
    ↓
个体参数修正
    ↓
穴位位置输出
    ↓
专家修正
    ↓
数据记录
```

后续再加入：

```text
多相机三角测量
RGB-D/结构光深度图
体表三维重建
软组织/体型修正
机械臂坐标映射
```

---

# 三、推荐技术栈

请优先采用以下技术栈，除非有更好的理由。

## 前端

推荐：

- React / Next.js
- TypeScript
- HTML5 Canvas / WebGL / SVG Overlay
- WebRTC 摄像头输入
- Zustand 或 Redux 管理状态
- Tailwind CSS 构建 UI

前端负责：

- 摄像头画面显示；
- 骨架关键点叠加；
- 穴位点和经络线叠加；
- 专家拖拽修正；
- 患者参数输入；
- 处方数据展示；
- 传感器数据展示；
- 实时置信度展示。

---

## 后端

推荐：

- Python FastAPI
- WebSocket 实时通信
- OpenCV
- MediaPipe / YOLOv8-Pose / RTMPose / MMPose 可选
- Pydantic 数据结构校验
- SQLite/PostgreSQL 存储 MVP 数据
- 文件方式加载穴位定义 JSON/YAML

后端负责：

- 图像帧接收；
- 姿态估计；
- 人体朝向判断；
- 穴位推算；
- 参数修正；
- 专家修正记录；
- 数据保存；
- 算法版本管理；
- 后续多相机/深度相机接口。

---

## 姿态估计算法选择

请对以下方案做初步比较，并建议 MVP 优先方案：

### 方案 A：MediaPipe Pose / Holistic

优点：

- 上手最快；
- 支持浏览器端或 Python 端；
- 有人体、手部、面部关键点；
- 适合快速 Demo。

缺点：

- 医疗精度有限；
- 遮挡和复杂姿态下不稳定；
- 对背面识别和局部穴位定位需要额外规则。

MVP 优先建议：可以作为第一版首选。

---

### 方案 B：YOLOv8-Pose

优点：

- 工程部署成熟；
- 检测速度快；
- 可本地部署；
- 对人体检测稳定。

缺点：

- 关键点数量较少；
- 手部细节不够；
- 穴位定位需要额外规则。

适合做人整体姿态辅助。

---

### 方案 C：MMPose / RTMPose

优点：

- 精度高；
- 可训练；
- 适合后续自定义数据集；
- 工业化能力更强。

缺点：

- 初始集成复杂；
- 部署成本高于 MediaPipe。

适合作为第二阶段升级。

---

## MVP 推荐

第一版建议：

```text
MediaPipe Holistic / Pose + Hands
```

原因：

- 快速验证；
- 同时支持人体骨架和手部关键点；
- 适合浏览器实时显示；
- 便于判断人体正反面和手掌/手背；
- 后续可替换为 MMPose/RTMPose。

请把姿态估计模块抽象成接口，避免未来替换模型时重写系统。

---

# 四、核心模块设计

请按模块化方式设计系统。

---

## Module 1：Camera Input 摄像头输入模块

功能：

- 支持浏览器调用本地摄像头；
- 支持上传图片；
- 支持上传视频；
- 支持 RTSP/USB 摄像头扩展；
- 后续支持多相机输入。

数据结构示例：

```json
{
  "camera_id": "cam_001",
  "camera_type": "rgb",
  "frame_id": "frame_000001",
  "timestamp": 1710000000.123,
  "resolution": {
    "width": 1280,
    "height": 720
  },
  "image_format": "rgb"
}
```

预留字段：

```json
{
  "intrinsics": null,
  "extrinsics": null,
  "depth_available": false,
  "depth_frame_id": null
}
```

---

## Module 2：Pose Estimation 人体骨架识别模块

功能：

- 输入 RGB 图像；
- 输出人体关键点；
- 输出每个关键点置信度；
- 支持多人时选择主目标；
- 支持人体框；
- 支持姿态稳定性判断。

关键点数据结构：

```json
{
  "pose_model": "mediapipe_holistic_v1",
  "algorithm_version": "0.1.0",
  "body_keypoints": [
    {
      "name": "left_shoulder",
      "x": 0.35,
      "y": 0.42,
      "z": null,
      "visibility": 0.92,
      "confidence": 0.91
    }
  ]
}
```

注意：

- 第一阶段 x/y 用归一化图像坐标；
- z 可以先为空或使用 MediaPipe 的相对 z；
- 后续结构光相机接入后，z 使用真实深度。

---

## Module 3：Body Orientation 人体正反面判断模块

需要实现人体朝向判断，输出：

```text
front
back
left_side
right_side
unknown
```

初始算法可以基于：

- 面部关键点是否可见；
- 鼻子/眼睛/嘴巴关键点置信度；
- 左右肩顺序；
- 左右髋顺序；
- 手臂关键点可见性；
- 躯干关键点对称关系；
- 背面时面部关键点不可见，但肩髋轮廓存在；
- 侧面时左右肩/髋距离显著压缩。

输出数据：

```json
{
  "body_orientation": "front",
  "confidence": 0.86,
  "reason": [
    "face_keypoints_visible",
    "left_right_shoulder_order_consistent",
    "torso_symmetry_high"
  ]
}
```

要求：

- 不要强行判断；
- 低置信度时输出 unknown；
- 该结果会影响穴位显示范围；
- 背面穴位只在 back 置信度足够时显示；
- 正面穴位只在 front 置信度足够时显示。

---

## Module 4：Hand Orientation 手掌/手背判断模块

需要实现左右手的手掌/手背判断。

输出：

```text
palm
back_of_hand
side
unknown
```

初始算法可以基于：

- MediaPipe Hands 关键点；
- 拇指与小指相对位置；
- 手指关节拓扑；
- 左右手标签；
- 手掌法向近似；
- 手部关键点可见性；
- 手指弯曲程度；
- 是否看到掌心纹理可作为后续视觉分类模型。

输出结构：

```json
{
  "hand_id": "left_hand",
  "orientation": "palm",
  "confidence": 0.78,
  "reason": [
    "thumb_pinky_relative_position",
    "landmark_topology"
  ]
}
```

要求：

- 第一版可以用启发式算法；
- 预留后续 CNN/ViT 手掌手背分类模型接口；
- 手部穴位只在朝向匹配时显示。

---

## Module 5：Patient Profile 患者参数输入模块

浏览器界面应支持输入：

```json
{
  "patient_id": "p_001",
  "height_cm": 170,
  "weight_kg": 65,
  "age": 35,
  "sex": "male",
  "bmi": 22.5,
  "body_type": "normal",
  "notes": ""
}
```

系统应根据身高、体重、年龄、性别对穴位推算做修正。

第一版修正逻辑可以是规则型，不要求训练模型。

---

## Module 6：Body Parameter Correction 个体参数修正模块

根据患者输入参数，对穴位定位做修正。

初始规则建议：

### 身高

影响：

- 整体骨架比例；
- 同身寸换算；
- 四肢长度；
- 躯干长度。

规则：

```text
同身寸基准优先从当前图像骨架估算；
若关键点缺失，则使用身高作为补充估计。
```

---

### 体重 / BMI

影响：

- 体表轮廓；
- 软组织厚度；
- 穴位体表投影偏移；
- 按压刺激深度建议。

初始处理：

```text
BMI 偏高时，穴位点位置信度降低；
部分穴位区域半径增大；
提示需要理疗师确认；
后续深度相机接入后再做三维修正。
```

---

### 年龄

影响：

- 皮肤/软组织弹性；
- 骨性标志可见性；
- 安全提示；
- 理疗强度建议。

初始处理：

```text
高龄用户降低推荐刺激强度；
增加风险提示；
穴位定位本身暂不大幅修正。
```

---

### 性别

影响：

- 体型比例；
- 特定区域禁忌；
- 部分穴位/处方注意事项。

初始处理：

```text
第一版仅作为规则和风险提示输入；
不做强模型偏移，避免伪科学过拟合。
```

输出结构：

```json
{
  "correction_factors": {
    "height_scale": 1.03,
    "bmi_confidence_penalty": 0.08,
    "age_safety_level": "normal",
    "sex_specific_warning": []
  }
}
```

---

## Module 7：Acupoint Definition 穴位定义文件模块

穴位必须从单独文件加载，不要硬编码在主程序里。

支持 JSON 或 YAML。

文件示例：

```json
{
  "version": "0.1.0",
  "source": "internal_rule_based_definition",
  "coordinate_system": "relative_body_landmark",
  "acupoints": [
    {
      "id": "LI4",
      "name_cn": "合谷",
      "name_en": "Hegu",
      "meridian": "Large Intestine Meridian",
      "body_side": "left_or_right",
      "visible_orientation": ["palm", "back_of_hand"],
      "region": "hand",
      "definition_method": "relative_landmark_and_cun",
      "landmark_rules": [
        {
          "type": "between_landmarks",
          "landmark_a": "thumb_mcp",
          "landmark_b": "index_mcp",
          "ratio": 0.5
        }
      ],
      "cun_rules": [],
      "default_radius_mm": 10,
      "safety_level": "low",
      "requires_expert_confirm": true
    }
  ]
}
```

必须支持：

- 穴位 ID；
- 中文名；
- 英文名；
- 所属经络；
- 正面/背面/手掌/手背可见条件；
- 依赖的人体关键点；
- 同身寸规则；
- 默认作用半径；
- 是否需要专家确认；
- 禁忌提示；
- 版本号；
- 来源说明。

---

## Module 8：Cun Measurement 同身寸计算模块

实现同身寸估算。

第一版应支持多种同身寸来源：

1. 基于用户身高估算；
2. 基于图像骨架长度估算；
3. 基于局部人体部位比例估算；
4. 基于专家手动校准。

输出结构：

```json
{
  "cun_estimates": [
    {
      "method": "skeleton_forearm_ratio",
      "cun_px": 23.4,
      "confidence": 0.82
    },
    {
      "method": "height_based_estimate",
      "cun_px": 21.8,
      "confidence": 0.55
    }
  ],
  "selected_cun": {
    "method": "skeleton_forearm_ratio",
    "cun_px": 23.4,
    "confidence": 0.82
  }
}
```

要求：

- 不同身体区域可以有不同的局部同身寸；
- 不要全身只用一个固定比例；
- 低置信度时提示人工确认；
- 专家可以手动校准同身寸。

---

## Module 9：Acupoint Estimation 穴位推算模块

输入：

- RGB 图像；
- 骨架关键点；
- 手部关键点；
- 人体正反面判断；
- 手掌/手背判断；
- 患者参数；
- 穴位定义文件；
- 同身寸估算；
- 处方需要的穴位列表。

输出：

```json
{
  "frame_id": "frame_000001",
  "acupoints": [
    {
      "id": "LI4",
      "name_cn": "合谷",
      "x": 0.512,
      "y": 0.631,
      "z": null,
      "coordinate_type": "image_normalized",
      "radius_px": 18,
      "confidence": 0.74,
      "source": "rule_based_cun_from_hand_landmarks",
      "orientation_valid": true,
      "requires_expert_confirm": true,
      "warnings": []
    }
  ]
}
```

要求：

- 不满足正反面/手掌手背条件时，不显示或灰显；
- 置信度低时显示为虚线区域；
- 对缺失关键点输出原因；
- 不要静默失败。

---

## Module 10：Expert Correction 专家修正模块

浏览器界面支持专家对穴位进行修正：

操作方式：

- 拖动穴位点；
- 点击新位置；
- 修改作用区域半径；
- 标记“确认正确”；
- 标记“AI 错误”；
- 输入修正原因；
- 选择原因标签。

修正原因标签包括：

```text
体型差异
姿态差异
关键点识别错误
同身寸估算错误
左右侧判断错误
正反面判断错误
手掌手背判断错误
专家经验判断
穴位定义文件错误
图像遮挡
其他
```

保存结构：

```json
{
  "correction_id": "corr_001",
  "timestamp": 1710000000.123,
  "expert_id": "expert_001",
  "patient_id": "p_001",
  "frame_id": "frame_000001",
  "acupoint_id": "LI4",
  "ai_position": {
    "x": 0.512,
    "y": 0.631,
    "z": null
  },
  "corrected_position": {
    "x": 0.534,
    "y": 0.622,
    "z": null
  },
  "correction_distance_px": 24.1,
  "correction_reason": ["同身寸估算错误", "专家经验判断"],
  "expert_confidence": 0.9,
  "notes": "位置应更靠近第二掌骨桡侧中点",
  "algorithm_version": "0.1.0",
  "acupoint_definition_version": "0.1.0"
}
```

要求：

- 必须保留 AI 原始位置；
- 必须保留专家修正位置；
- 必须记录算法版本；
- 必须记录穴位定义版本；
- 必须记录修正原因；
- 数据应可导出为 JSON/CSV；
- 未来可用于训练模型。

---

## Module 11：Prescription 诊疗处方数据模块

支持加载患者本次诊疗处方。

示例：

```json
{
  "prescription_id": "rx_001",
  "patient_id": "p_001",
  "diagnosis": "肩颈紧张",
  "target_regions": ["neck", "shoulder", "upper_back"],
  "recommended_acupoints": ["GB20", "GB21", "SI11"],
  "therapy_plan": [
    {
      "step": 1,
      "region": "neck",
      "device": "warm_vibration_terminal",
      "duration_sec": 180,
      "intensity": "low",
      "notes": "询问酸胀感"
    }
  ],
  "contraindications": [],
  "created_by": "doctor_001"
}
```

浏览器界面应显示：

- 当前诊断；
- 推荐穴位；
- 当前步骤；
- 推荐理疗终端；
- 推荐时长；
- 风险提示；
- 理疗师沟通提示词。

---

## Module 12：Sensor Data 传感器数据模块

预留传感器数据输入接口。

未来可能包括：

- 压力；
- 温度；
- 震动频率；
- 终端姿态；
- 接触时间；
- 轨迹；
- 患者反馈按钮；
- 心率/皮电等生理信号。

第一版可用 mock 数据。

数据结构：

```json
{
  "sensor_id": "pressure_001",
  "device_id": "terminal_001",
  "timestamp": 1710000000.123,
  "type": "pressure",
  "value": 12.4,
  "unit": "N",
  "status": "normal"
}
```

浏览器界面需要预留实时展示区域。

---

## Module 13：Visualization 浏览器实时可视化模块

界面建议分为：

```text
左侧：实时摄像头画面 + 骨架 + 穴位 + 经络叠加
右侧上：患者信息
右侧中：诊疗处方
右侧下：传感器数据
底部：日志/置信度/专家修正记录
```

实时画面叠加内容：

- 人体骨架点和线；
- 手部关键点；
- 人体朝向标签；
- 手掌/手背标签；
- 穴位中心点；
- 穴位作用区域；
- 穴位名称；
- 置信度；
- 经络路径；
- 低置信度警告；
- 专家修正点；
- AI 原始点和专家修正点连线。

视觉规则：

```text
高置信度：实线圆
中置信度：半透明圆
低置信度：虚线圆 + 需要确认
专家修正：蓝色点
AI 原始点：黄色点
禁忌/风险：红色提示
```

---

# 五、深度数据与多相机预留接口

虽然第一版基于 RGB，但必须预留后续接口。

---

## Multi-Camera Interface

数据结构：

```json
{
  "camera_group_id": "group_001",
  "cameras": [
    {
      "camera_id": "cam_front",
      "type": "rgb",
      "intrinsics": {},
      "extrinsics": {},
      "sync_status": "synced"
    },
    {
      "camera_id": "cam_side",
      "type": "rgb",
      "intrinsics": {},
      "extrinsics": {},
      "sync_status": "synced"
    }
  ]
}
```

预留功能：

- 多相机标定；
- 多视角关键点融合；
- 遮挡补偿；
- 三角测量；
- 人体表面粗三维重建。

---

## Depth Camera / Structured Light Interface

数据结构：

```json
{
  "depth_frame_id": "depth_000001",
  "camera_id": "structured_light_001",
  "timestamp": 1710000000.123,
  "depth_map": null,
  "point_cloud": null,
  "unit": "mm",
  "alignment_to_rgb": "registered"
}
```

后续功能：

- RGB 与深度对齐；
- 穴位二维点投影到三维体表；
- 体表法向估计；
- 曲面修正；
- BMI/软组织厚度修正；
- 投影/振镜坐标校正；
- 机械臂坐标映射。

---

## Acupoint 3D Correction Interface

未来深度修正输出：

```json
{
  "acupoint_id": "GB21",
  "image_position": {
    "x": 0.45,
    "y": 0.38
  },
  "surface_3d_position": {
    "x_mm": 123.4,
    "y_mm": 54.2,
    "z_mm": 842.1
  },
  "surface_normal": {
    "nx": 0.12,
    "ny": -0.33,
    "nz": 0.94
  },
  "depth_confidence": 0.81,
  "correction_applied": true,
  "correction_reason": "surface_curvature_compensation"
}
```

---

# 六、数据保存和版本管理

系统必须保存以下数据：

1. 患者参数；
2. 原始帧 ID；
3. 姿态关键点；
4. 人体朝向判断结果；
5. 手掌/手背判断结果；
6. 同身寸估算结果；
7. 穴位定义文件版本；
8. AI 原始穴位推算结果；
9. 专家修正结果；
10. 诊疗处方；
11. 传感器数据；
12. 算法版本；
13. 操作日志。

所有数据应可导出。

建议目录结构：

```text
project/
  frontend/
  backend/
  models/
  data/
    acupoint_definitions/
      acupoints_v0.1.json
    prescriptions/
    patients/
    corrections/
    sessions/
  docs/
  tests/
```

---

# 七、API 设计建议

## 1. 上传/获取患者参数

```http
POST /api/patient/profile
GET /api/patient/{patient_id}
```

---

## 2. 获取穴位定义

```http
GET /api/acupoints/definitions
POST /api/acupoints/definitions/reload
```

---

## 3. 姿态估计

```http
POST /api/vision/pose-estimate
```

---

## 4. 实时 WebSocket

```http
WS /ws/realtime
```

传输：

- 视频帧；
- 姿态结果；
- 穴位结果；
- 传感器数据；
- 专家修正事件。

---

## 5. 专家修正

```http
POST /api/expert/correction
GET /api/expert/corrections?patient_id=xxx
```

---

## 6. 诊疗处方

```http
POST /api/prescription
GET /api/prescription/{patient_id}
```

---

## 7. 传感器数据

```http
POST /api/sensors/data
GET /api/sensors/realtime
```

---

# 八、第一版 Demo 范围

第一版不要做太大。

请优先实现以下 Demo：

## Demo 1：正面人体穴位显示

- 摄像头识别人正面；
- 显示人体骨架；
- 判断 front；
- 加载正面穴位定义；
- 显示 5-10 个示例穴位；
- 支持专家拖动修正。

---

## Demo 2：背面人体穴位显示

- 摄像头识别人背面；
- 判断 back；
- 显示背部示例穴位；
- 显示置信度；
- 支持专家修正。

---

## Demo 3：手部穴位显示

- 识别手部；
- 判断手掌/手背；
- 显示合谷、劳宫等示例穴位；
- 支持左右手；
- 支持专家修正。

---

## Demo 4：患者参数修正

- 输入身高体重年龄性别；
- 显示 BMI；
- 对穴位置信度/作用半径做规则修正；
- 显示修正原因。

---

## Demo 5：处方 + 传感器 mock 展示

- 加载一个肩颈理疗处方；
- 显示推荐穴位；
- 显示 mock 压力/温度/震动数据；
- 在浏览器中同步呈现。

---

# 九、初始穴位样例

请先实现少量穴位，不要一次性做全身。

建议第一版穴位：

## 手部

- 合谷 LI4
- 劳宫 PC8

## 肩颈背部

- 风池 GB20
- 肩井 GB21
- 天宗 SI11
- 大椎 GV14

## 前臂/腿部

- 内关 PC6
- 足三里 ST36
- 三阴交 SP6

要求：

- 每个穴位都在定义文件中；
- 每个穴位有定位规则；
- 没有足够关键点时给出原因；
- 允许人工修正。

---

# 十、重要实现注意事项

## 1. 不要伪装成医疗诊断系统

界面应提示：

```text
当前系统为理疗辅助导航原型，不作为独立医疗诊断或自动治疗依据。
穴位位置仅为算法推荐，需要专业人员确认。
```

---

## 2. 不要承诺精确穴位定位

第一版显示：

```text
推荐作用区域
```

而不是：

```text
绝对精准穴位点
```

---

## 3. 所有算法输出都要带置信度

包括：

- 人体关键点；
- 人体朝向；
- 手掌/手背；
- 同身寸；
- 穴位位置；
- 深度修正；
- 专家确认。

---

## 4. 低置信度要显式提示

不要隐藏失败。

示例：

```text
无法稳定识别右肩关键点，因此肩井穴位置信度降低，需要专家确认。
```

---

## 5. 所有专家修正必须可追踪

不要只覆盖 AI 结果。

必须保留：

```text
AI 原始结果
专家修正结果
修正原因
专家 ID
时间
算法版本
穴位定义版本
患者参数
```

---

# 十一、请你输出的内容

请按以下顺序输出：

## 1. 总体技术架构图

用文字或 Mermaid 描述：

```text
Camera → Pose → Orientation → Cun → Acupoint Estimation → Visualization → Expert Correction → Data Store
```

---

## 2. 推荐技术栈和理由

说明为什么第一版选 MediaPipe / FastAPI / React / WebSocket。

---

## 3. 模块划分

逐个列出模块职责、输入、输出。

---

## 4. 数据结构定义

至少包括：

- PatientProfile
- FrameData
- BodyKeypoint
- HandKeypoint
- BodyOrientation
- HandOrientation
- CunEstimate
- AcupointDefinition
- AcupointEstimate
- ExpertCorrection
- Prescription
- SensorData
- DepthFrame
- CameraCalibration

---

## 5. API 设计

列出 REST 和 WebSocket API。

---

## 6. 前端页面设计

说明页面布局、交互方式和实时可视化策略。

---

## 7. 算法 MVP 实现策略

包括：

- 姿态估计；
- 正反面判断；
- 手掌手背判断；
- 同身寸估算；
- 穴位推算；
- 个体参数修正；
- 专家修正学习。

---

## 8. 第一阶段开发任务拆分

按 1-2 周 Sprint 拆分。

建议：

### Sprint 1

- 摄像头输入；
- MediaPipe 骨架识别；
- 浏览器画面叠加；
- 基础后端。

### Sprint 2

- 正反面判断；
- 手掌手背判断；
- 穴位定义文件；
- 示例穴位显示。

### Sprint 3

- 同身寸计算；
- 患者参数输入；
- 个体参数修正；
- 置信度显示。

### Sprint 4

- 专家修正；
- 数据保存；
- 处方显示；
- 传感器 mock；
- 导出数据。

---

## 9. 风险清单

请列出技术风险：

- RGB 单目精度不足；
- 背面识别不稳定；
- 手掌手背判断不稳定；
- 穴位定义主观性；
- 专家标注不一致；
- 患者微动；
- 遮挡；
- 光照；
- 体型差异；
- 数据噪声。

并给出缓解策略。

---

## 10. 可运行 Demo 代码骨架

请尽量生成可运行的初始代码结构，包括：

```text
frontend/
backend/
data/acupoint_definitions/acupoints_v0.1.json
README.md
```

如果无法一次性生成完整代码，请先生成目录结构、核心接口、核心数据模型和关键伪代码。

---

# 十二、最终系统设计原则

请始终遵守以下原则：

1. 第一版追求可验证，不追求医疗级精度；
2. 算法输出必须有置信度；
3. 穴位显示为推荐区域，而不是绝对点；
4. 专家修正数据必须保留 AI 原始结果；
5. 穴位定义必须外部文件化；
6. 同身寸规则必须模块化；
7. 人体正反面和手掌手背判断必须可解释；
8. 身高体重年龄性别先作为规则修正，不要过度机器学习；
9. 所有模块要预留三维深度数据接口；
10. 浏览器界面必须支持实时图像、传感器数据和处方数据同步显示；
11. 当前系统定位为理疗辅助导航原型，不是自动诊断或自动治疗系统；
12. 整体架构要能从 RGB MVP 平滑升级到 RGB-D / 结构光 / 多相机 / 机械臂接口。





请不要一开始追求复杂医疗级模型，也不要直接做机械臂或自动针灸。当前最重要的是：用 RGB 相机快速验证“人体骨架 → 朝向判断 → 同身寸规则 → 穴位推荐区域 → 专家修正 → 浏览器实时呈现 → 数据沉淀”这条链路是否跑通。



可以让 Agent 先输出

1. 系统目录结构
2. FastAPI 数据模型
3. React 页面草图
4. acupoints_v0.1.json 示例文件
5. MediaPipe 姿态估计 Demo
