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


# 十三、补充规范（审计盲区 B1~B17）

> 以下 17 条规范来自 `project-audit-report.md` 审计结果，按优先级 P0 > P1 > P2 排列。
> 每条包含「问题描述 → 规范要求 → 实现方式 → 验收标准」。

---

## B1 · 会话并发隔离（P0）

**问题**：当前 `ws/handler.py` 使用全局变量 `_current_patient`、`_current_definitions`、`_expert_corrections` 管理会话状态。当多个 WebSocket 连接同时存在时（多页面、多人），全局状态会被覆盖，导致患者 A 看到患者 B 的数据。

**规范要求**：
- 每个 WebSocket 连接必须拥有独立的会话上下文（Session Context）
- 一个连接的生命周期 = 一次完整的穴位识别会话
- 会话上下文包括：`patient`、`definitions`、`corrections`、`processing_state`
- 连接断开时，会话上下文必须在合理时间内（默认 300s）被 GC

**实现方式**：
- 新建 `backend/services/session_service.py`，实现 `SessionContext` 数据类
- `ws_handler` 为每个 `websocket` 创建独立的 `SessionContext` 实例
- REST API 通过 `session_id` 参数访问指定会话的数据
- 提供 `session_id → SessionContext` 的弱引用映射，支持超时自动清理

**验收标准**：
- 两个浏览器 Tab 连接同一 ws 端点，各自发送不同 patient 参数，互不干扰
- 一个连接断开后，该会话在 300s 内被从内存中移除

---

## B2 · 帧背压控制规范（P0）

**问题**：前端 `setInterval` 每 150ms 无脑发帧，后端没有任何流量控制。当后端处理速度跟不上时，帧队列堆积导致内存溢出和延迟雪崩。

**规范要求**：
- 前端：上一帧的 `result` 回执未到达前，禁止发送下一帧
- 后端：当 `is_processing == True` 时，收到的帧直接丢弃并回复 `{type: "skip"}`
- 帧间间隔下限：150ms（即使处理速度更快也不加速）
- 帧超时：单帧处理超过 1000ms 时主动丢弃并回复 `{type: "timeout"}`

**实现方式**：
- 前端维护 `pendingFrame: boolean` 锁
  - `sendFrame` 发送前 `assert(!pendingFrame)`，发送后设 `true`
  - 收到 `result` / `skip` / `timeout` 消息时，将 `pendingFrame` 设回 `false`
- 后端 `_process_frame` 入口加 `is_processing` 标志保护
  - 处理开始设 `True`，处理结束/异常/超时设 `False`
  - 超时使用 `asyncio.wait_for(process, timeout=1.0)`

**验收标准**：
- 慢 CPU 环境下不出现内存持续增长
- 前端控制台无连续 3 帧以上 "skip" 日志
- 帧间间隔稳定在 150~160ms（见 B16 性能基线）

---

## B3 · 数据隐私规范（P0）

**问题**：当前患者身体参数（身高、体重）和摄像头画面都通过 WebSocket 明文传输，无任何脱敏或访问控制。

**规范要求**：
- **MVP/内网阶段**：至少确认所有数据在本地链路传输，不上传云端
- 患者 `face_landmarks` 不在服务端持久化存储
- 摄像头画面帧不得写入磁盘（仅在内存中处理）
- 患者数据导出功能必须带有「匿名化」开关，去除 `patient_id`、`face_landmarks`

**实现方式**：
- `config.py` 增加 `DATA_RETENTION_POLICY` 配置块：
  ```python
  STORE_FRAMES_TO_DISK = False       # 帧不落盘
  STRIP_FACE_LANDMARKS = True        # 导出时剥离面部特征点
  KEEP_PATIENT_ID_IN_EXPORT = False  # 导出时移除患者 ID
  ```
- 所有 `cv2.imwrite` / `open(..., "wb")` 写帧操作在正式模式禁止

**验收标准**：
- `backend/` 目录下及 `/tmp/` 下无 `.jpg`/`.png` 帧文件残留
- 导出 JSON 中不含 `face_landmarks` 字段

---

## B4 · 启动失败降级（P0）

**问题**：当前启动流程无显式错误处理——YOLO 模型加载失败、acupoints 文件缺失、MediaPipe 初始化失败都会导致静默崩溃或 500。

**规范要求**：
- 启动时**必须**显式检查三项核心依赖：
  - `yolo_model`：YOLO 模型加载成功
  - `mediapipe_hands`：MediaPipe Hands 初始化成功
  - `acupoint_definitions`：穴位定义 JSON 解析成功
- 任何一项失败 → 服务以 "degraded" 模式启动，`/api/health` 返回具体失败原因
- YOLO 模型失败时，WebSocket `/ws/realtime` 端点返回 error message 而非静默断连
- 所有关键错误必须写入结构化日志（JSON 格式），包含时间戳、错误类型、堆栈

**实现方式**：
- 新增 `modules/startup_health.py`：
  ```python
  async def check_yolo_ready() -> bool: ...
  async def check_mediapipe_ready() -> bool: ...
  async def check_definitions_loaded() -> bool: ...
  async def deep_health_check() -> dict: ...
  ```
- `health_check()` 端点返回深度检查结果：
  ```json
  {
    "status": "degraded",
    "yolo_ready": true,
    "mediapipe_ready": true,
    "definitions_loaded": false,
    "definitions_error": "FileNotFoundError: ...",
    "uptime_seconds": 120
  }
  ```

**验收标准**：
- 删除 `acupoints_v0.1.json` 后启动，`/api/health` 返回 `definitions_loaded: false`
- 服务不崩溃，WebSocket 连接建立但返回错误提示

---

## B5 · 专家权限控制（P1）

**问题**：当前任何人建立 WebSocket 连接后都可以发送 `expert_correction` 消息，无任何身份验证。

**规范要求**：
- MVP/内网阶段：前端设置 `X-Expert-Token` header 或 URL query parameter
- 后端校验 token，非专家用户发送的 `expert_correction` 消息返回 403 并记录日志
- token 从 `config.py` 的 `EXPERT_TOKENS` 列表读取
- 生产环境切换为 JWT 或 OAuth2

**实现方式**：
- `config.py` 增加：
  ```python
  EXPERT_TOKENS = ["dev-expert-token"]  # 内网测试用
  ```
- `ws/handler.py` 解析 `X-Expert-Token` query parameter
- 对 `expert_correction` 消息校验 token，不匹配返回 `{type: "error", code: 403, detail: "permission denied"}`

**验收标准**：
- 不带 token 的 WebSocket 发送 `expert_correction` 收到 403
- 带正确 token 的 WebSocket 发送 `expert_correction` 正常处理

---

## B6 · 处方版本化（P1）

**问题**：`acupoints_v0.1.json` 热加载后，之前基于旧定义生成的修正记录 (`correction_store`) 与新定义可能语义不兼容（穴位被删除、坐标锚点变化）。

**规范要求**：
- `acupoints_v0.1.json` 文件顶部增加 `version` 字段（如 `"version": "0.1.0"`）
- `correction_store` 中每条记录关联 `definition_version`
- 热加载后自动检测版本变更：
  - 小版本（patch）更新：旧修正继续有效
  - 中版本（minor）更新：标记旧修正为 "needs_review"
  - 大版本（major）更新：清空所有旧修正，备份到 `corrections_v{N}.json`

**实现方式**：
- `AcupointDefinitions` Pydantic model 增加 `version: str` 字段
- `CorrectionRecord` 增加 `definition_version: Optional[str]`
- `reload_definitions()` 比较新旧版本号，按 SemVer 规则执行清理策略

**验收标准**：
- 热加载 `v0.1.0` → `v0.1.1`：旧修正保留
- 热加载 `v0.1.0` → `v0.2.0`：旧修正标记 `needs_review`
- 热加载 `v0.1.0` → `v1.0.0`：旧修正备份并清空

---

## B7 · 多人场景主目标规则（P1）

**问题**：MediaPipe 可能在一帧中检出多个人体骨架。当前代码默认取第一个检测结果，没有明确的多目标策略。

**规范要求**：
- 核心规则：**始终以画面中检测到的第一个正对相机、姿态最完整的人体为主目标**
- 主目标选择算法：
  1. 过滤：去除姿态置信度 < 0.5 的检测结果
  2. 排序：按 `前方朝向得分`（身体正对相机程度）降序排列
  3. 取排序结果的第一个作为主目标
- 前方朝向得分的计算方式：
  - 左右肩关键点 Y 坐标差值越小 → 越可能是正面朝向
  - 鼻子 z 坐标（如果可用）越接近 0 → 越居中
- 非主目标在 overlay 上以灰色虚线圈出，标注 "Secondary"

**实现方式**：
- `ws/handler.py` 或专用模块 `modules/multi_person.py` 实现 `select_primary_subject(results) -> Subject`
- `overlay render` 根据 `Subject.role` 渲染不同颜色：
  - Primary：绿色实线 + 穴位标签
  - Secondary：灰色虚线，不标注穴位

**验收标准**：
- 画面中有 2 人（一人正面、一人侧面），穴位标注在正面的人身上
- 画面中 1 人的姿态置信度 < 0.5，不做任何标注

---

## B8 · 热加载幂等性（P1）

**问题**：`POST /api/acupoints/definitions/reload` 正在被调用期间，如果有 WebSocket 帧在并发处理中，`reload_definitions()` 会直接替换全局 `_current_definitions`，导致正在运行的帧推理函数读到半新半旧的数据。

**规范要求**：
- 热加载操作必须获取全局读-写锁，与帧处理互斥
- 调用 `reload` 时：
  - 新请求被排队等待
  - 当前正在处理的帧完成后再替换定义
  - 替换完成后，下一个被排队的请求使用新定义

**实现方式**：
- `session_service.py` 使用 `asyncio.Lock`：
  ```python
  _definitions_lock = asyncio.Lock()
  
  async def reload_definitions():
      async with _definitions_lock:
          # 原子替换
          _current_definitions = load_acupoint_definitions()
  
  async def _process_frame(frame):
      async with _definitions_lock:
          definitions = _current_definitions  # 快照引用
      # 后续使用 definitions 快照进行推理
  ```

**验收标准**：
- 在帧处理密集期间（QPS > 5）连续调用 3 次 `/reload`，无 KeyError 或空数据异常

---

## B9 · 同身寸聚合策略（P1）

**问题**：同一穴位有多种计算方法（骨度分寸法、手指同身寸法、体表标志法），当前代码对 `_get_kp` 的调用结果取均值，没有加权策略和兜底逻辑。

**规范要求**：
- 分级权重（从高到低）：
  1. **骨度折量法**（权重 0.5）：基于实际骨骼长度测量，最精确
  2. **体表标志法**（权重 0.3）：基于解剖标志（肚脐、乳头、肩峰等）
  3. **手指同身寸法**（权重 0.2）：基于患者手指宽度推算，精度最低
- 缺失数据的处理：
  - 骨骼关键点不可见时，对应的测量方法跳过（不参与加权）
  - 所有方法都不可用时，返回 `confidence: 0` + fallback 体位估计坐标

**实现方式**：
- `modules/cun_measurement.py` 中 `compute_acupoint_position` 函数实现三级加权
- 返回结构包含每种方法的计算结果和最终加权结果：
  ```python
  {
    "final_position": (x, y),
    "confidence": 0.85,
    "methods": {
      "bone_proportional": {"position": ..., "confidence": 0.9, "weight": 0.5},
      "body_landmark": {"position": ..., "confidence": 0.8, "weight": 0.3},
      "finger_cun": None  # 此方法不可用
    }
  }
  ```

**验收标准**：
- 三法全可用时，最终位置 ∈ 三种方法的 convex hull
- 只有一种方法可用时，权重退化为 1.0

---

## B10 · 穴位格式校验（P1）

**问题**：`acupoints_v0.1.json` 文件在热加载时没有 schema 校验，无效的 JSON 结构（缺失 `anchor`、坐标越界等）会导致运行时崩溃。

**规范要求**：
- 加载穴位定义时必须通过 Pydantic v2 的 `model_validate` 校验
- 每个 `Acupoint` 的必填字段：
  - `id`：穴位唯一标识，格式 `{meridian}_{name}`，如 `LU_zhongfu`
  - `name_zh`：中文名
  - `anchor`：相对于骨骼关键点的位置描述
  - `meridian`：所属经络
- 校验规则：
  - `anchor` 不能为空字符串
  - `side` 必须是 `"left"` / `"right"` / `"bilateral"` / `"central"` 之一
  - `safety_level` 必须是 `"safe"` / `"caution"` / `"danger"` 之一

**实现方式**：
- `schemas/models.py` 中 `Acupoint` 定义完整字段 + validator：
  ```python
  from pydantic import field_validator
  
  class Acupoint(BaseModel):
      id: str
      name_zh: str
      anchor: str
      meridian: str
      side: Literal["left", "right", "bilateral", "central"]
      safety_level: Literal["safe", "caution", "danger"]
      
      @field_validator("anchor")
      @classmethod
      def anchor_not_empty(cls, v):
          if not v.strip():
              raise ValueError("anchor 不能为空")
          return v
  ```

**验收标准**：
- 加载有字段缺失的 JSON 时，FastAPI 返回 422 + 详细错误字段
- 加载有效 JSON 正常，穴位数量 ≥ 1

---

## B11 · 浏览器兼容性（P2）

**问题**：前端使用了 `getUserMedia`、`WebSocket`、`OffscreenCanvas`、`requestAnimationFrame` 等 API，没有声明最低浏览器版本要求。

**规范要求**：
- 目标浏览器最低版本：
  - Chrome 90+
  - Edge 90+
  - Firefox 88+
  - Safari 15+（iOS/macOS）
- 不兼容时页面显示友好提示，列出不支持的特性：
  - `getUserMedia` → "您的浏览器不支持摄像头访问"
  - `WebSocket` → "您的浏览器不支持实时通信"
  - `OffscreenCanvas` → 回退到 `createElement('canvas')`，性能下降提示

**实现方式**：
- `index.html` 增加 `<noscript>` 标签
- `frontend/src/utils/browser-check.ts` 实现 `checkBrowserSupport()`：
  ```typescript
  export function checkBrowserSupport(): string[] {
    const missing: string[] = [];
    if (!navigator.mediaDevices?.getUserMedia) missing.push('getUserMedia');
    if (!('WebSocket' in window)) missing.push('WebSocket');
    if (!('OffscreenCanvas' in window)) missing.push('OffscreenCanvas');
    return missing;
  }
  ```
- 入口组件 `App.tsx` 的 `useEffect` 调用 `checkBrowserSupport()`，不兼容时渲染错误页

**验收标准**：
- IE 11 打开页面显示 "您的浏览器不受支持" + 缺少特性列表
- Chrome 90+ 打开正常加载，无警告

---

## B12 · 版本兼容性矩阵（P2）

**问题**：项目依赖 Python 3.10+、Node.js 16+、ultralytics 8.x、MediaPipe 0.10.x 等，但没有声明互操作版本矩阵。

**规范要求**：
- `pyproject.toml` / `requirements.txt` 必须锁定每个依赖的精确版本或兼容范围
- 版本矩阵应在 README 和 `prompt.md` 中显式列出
- 每次依赖升级后更新此矩阵

**实现方式**：

| 组件 | 最低版本 | 推荐版本 | 备注 |
|---|---|---|---|
| Python | 3.10 | 3.12+ | 3.9 及以下不支持 |
| Node.js | 16 | 18+ | 16 已 EOL |
| ultralytics | 8.0.0 | 8.2.x | 8.x 推荐 |
| mediapipe | 0.10.0 | 0.10.9+ | 0.9.x 架构不兼容 |
| FastAPI | 0.100.0 | 0.110+ | Pydantic v2 支持从 0.100 开始 |
| Pydantic | 2.0 | 2.7+ | model_validator 从 2.0 开始 |
| React | 18.0 | 18.3+ | Concurrent Mode 兼容 |
| Zustand | 4.4 | 4.5+ | 无需额外 peer deps |

**验收标准**：
- 使用矩阵中最低版本组合，`npm install` + `pip install` 无冲突
- 使用推荐版本组合，所有功能通过

---

## B13 · 坐标系归一化（P2）

**问题**：MediaPipe 输出归一化坐标 (0~1)，YOLO 输出像素坐标，绘图时 `OverlayCanvas` 需要在两种坐标系间转换。当前转换逻辑分散在多处，容易出现比例错误。

**规范要求**：
- 内部统一使用**归一化坐标** (0~1)，以画面左上角为原点
- 只有最终渲染 (OverlayCanvas) 时才转换为像素坐标
- 定义明确的转换函数：
  ```python
  def norm_to_pixel(x: float, y: float, width: int, height: int) -> tuple[int, int]: ...
  def pixel_to_norm(px: int, py: int, width: int, height: int) -> tuple[float, float]: ...
  ```

**实现方式**：
- `modules/coordinate_utils.py` 提供归一化/像素转换工具
- 所有内部计算（距离、比例、角度）使用归一化坐标
- `acupoints_v0.1.json` 中 `anchor` 的描述使用归一化坐标参考

**验收标准**：
- 窗口缩放时（1920×1080 → 800×600），穴位标注位置准确缩放
- 旋转画面后重新计算，穴位位置不离谱

---

## B14 · 导出格式标准（P2）

**问题**：当前无数据导出功能，未来需要支持穴位标注结果的导出。但没有定义导出格式标准。

**规范要求**：
- 导出格式：JSON Schema 声明的结构化 JSON
- 导出内容：
  - `session_metadata`：时间戳、会话 ID、患者参数
  - `acupoint_results`：穴位 ID → 坐标 → 置信度 → 修正记录
  - `skeleton_data`：骨架关键点列表（可选）
  - `raw_frames`：不导出（见 B3 隐私规范）
- 文件名格式：`acupoint_session_{session_id}_{timestamp}.json`
- 同时支持 CSV 简化版导出（穴位 ID, X, Y, 置信度）

**实现方式**：
- `schemas/export_schema.py` 定义 `SessionExport` Pydantic model
- `GET /api/session/{session_id}/export?format=json` 和 `?format=csv` 端点
- JSON export 附带 `$schema` 引用

**验收标准**：
- 导出 JSON 通过 JSON Schema 验证
- CSV 用 Excel 打开不乱码（UTF-8 BOM）

---

## B15 · 离线降级行为（P2）

**问题**：前端强依赖后端 WebSocket 连接，断网时页面直接无反应，没有任何离线提示或本地缓存。

**规范要求**：
- WebSocket 断开时：
  - 摄像头继续工作（本地预览不中断）
  - overlay 显示 "连接断开，正在重连..." 提示
  - 穴位标注区域显示上次成功结果（灰度显示，标注 "(缓存)"）
- 恢复连接后：
  - overlay 提示消失
  - 标注恢复实时更新

**实现方式**：
- `appStore.ts` 维护 `wsConnected: boolean` 和 `lastCachedResult: Result | null`
- `OverlayCanvas` 根据 `wsConnected` 切换渲染模式：
  - 在线：绿色标注 + 实时动画
  - 离线：灰色标注 + 静态显示 + "重连中" 水印
- 重连成功后 `lastCachedResult` 被新结果覆盖

**验收标准**：
- 拔网线后，摄像头画面不冻结，标注变灰
- 插回网线后，标注在 3s 内恢复绿色实时更新

---

## B16 · 性能指标基线（P2）

**问题**：没有定义性能基线，无法判断系统是否在正常范围内运行。

**规范要求**：
- MVP 阶段的性能基线（以 Chrome 90+ / Intel i5 / 8GB RAM / 1080p 摄像头为参考）：

| 指标 | 目标值 | 告警阈值 |
|---|---|---|
| 帧处理延迟 (端到端) | < 200ms | > 500ms |
| WebSocket 帧间隔 | 150~160ms | > 200ms 或 < 100ms |
| YOLO 推理耗时 | < 80ms | > 150ms |
| MediaPipe Hands 耗时 | < 30ms | > 60ms |
| 前端渲染帧率 | ≥ 25 FPS | < 15 FPS |
| 内存占用 (服务端) | < 500MB | > 1GB |
| 内存占用 (前端 Tab) | < 200MB | > 400MB |

**实现方式**：
- 后端内置性能统计模块 `modules/perf_monitor.py`：
  ```python
  @dataclass
  class FramePerf:
      yolo_ms: float
      mediapipe_ms: float
      compute_ms: float
      total_ms: float
  
  class PerfMonitor:
      def record(self, perf: FramePerf): ...
      def stats(self, window_seconds=30) -> PerfStats: ...
  ```
- 前端 `performance.now()` 测量帧往返时间
- `/api/health` 端点包含近 30 秒的性能统计

**验收标准**：
- 所有指标在实际运行中可见（`/api/health` 返回真值）
- 超过告警阈值时日志中输出 WARNING

---

## B17 · 穴位来源合规（P2）

**问题**：穴位定义数据来源的法律合规性和引用归属未声明。

**规范要求**：
- `acupoints_v0.1.json` 或 README 中**必须**声明数据来源：
  - 主要参考标准：《腧穴名称与定位》（GB/T 12346-2021）
  - 坐标计算基于公开的人体骨骼解剖学数据
  - 此项目输出为**穴位区域参考**，不是医疗诊断
- 所有页面底部或侧边栏显示免责声明：
  > ⚠️ 本系统仅供教学与研究参考，不构成医疗建议。实际针灸操作请咨询执业中医师。

**实现方式**：
- `acupoints_v0.1.json` 增加 `"_meta"` 字段：
  ```json
  {
    "_meta": {
      "source": "GB/T 12346-2021",
      "purpose": "educational_reference",
      "disclaimer": "不构成医疗建议"
    },
    "acupoints": [...]
  }
  ```
- 前端 `Footer` 或 `InfoPanel` 组件渲染免责声明

**验收标准**：
- README 中有数据来源声明章节
- 每个页面可见免责声明（非弹窗，为持久展示）

