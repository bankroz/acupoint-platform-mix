# AI 经络/穴位导航理疗系统 MVP

> 基于 **YOLOv8-Pose** 的人体穴位识别与导航原型系统

## 系统定位

当前为 **理疗辅助导航原型**，不作为独立医疗诊断或自动治疗依据。穴位位置仅为算法推荐区域，需要专业人员确认。

## 技术架构

```
浏览器摄像头 → WebSocket 帧传输 → FastAPI 后端
                                      ↓
                              YOLOv8-Pose 身体姿态估计
                              MediaPipe Hands 手部关键点
                                      ↓
                              人体朝向判断 (front/back/side)
                                      ↓
                              同身寸 (Cun) 估算
                                      ↓
                              穴位推算 (骨架关键点 + 规则)
                                      ↓
              ← WebSocket 返回结果 (骨架 + 穴位)
                                      ↓
浏览器 Canvas 叠加显示 ← 专家拖拽修正
```

## 项目结构

```
穴位识别/YOLOV8/
├── backend/                     # Python 后端
│   ├── main.py                 # FastAPI 入口
│   ├── config.py               # 集中配置
│   ├── requirements.txt        # Python 依赖
│   ├── modules/
│   │   ├── pose_estimator.py   # YOLOv8-Pose + MediaPipe Hands
│   │   ├── body_orientation.py # 人体朝向判断
│   │   ├── hand_orientation.py # 手掌/手背判断
│   │   ├── cun_measurement.py  # 同身寸计算
│   │   ├── acupoint_estimator.py # 穴位推算引擎
│   │   └── correction_store.py # 修正数据存储
│   ├── schemas/
│   │   └── models.py           # Pydantic 数据模型
│   └── ws/
│       └── handler.py          # WebSocket 实时处理
├── frontend/                    # React 前端
│   └── src/
│       ├── App.tsx             # 主页面
│       ├── components/
│       │   ├── CameraView.tsx   # 摄像头 + Canvas
│       │   ├── OverlayCanvas.tsx # 可视化叠加
│       │   ├── PatientPanel.tsx  # 患者参数
│       │   ├── ExpertPanel.tsx   # 专家修正
│       │   ├── PrescriptionPanel.tsx # 处方
│       │   └── SensorPanel.tsx  # 传感器 Mock
│       └── ...
├── data/
│   └── acupoint_definitions/
│       └── acupoints_v0.1.json # 穴位定义
└── README.md
```

## 快速启动

### 1. 后端

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt

# 启动后端 (首次运行会自动下载 YOLOv8n-pose 模型 ~4MB)
python main.py
```

后端启动在 `http://0.0.0.0:8765`

### 2. 前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端启动在 `http://localhost:5173`

### 3. 使用

1. 打开浏览器访问 `http://localhost:5173`
2. 点击「开启摄像头」按钮
3. 系统会自动：
   - 检测人体骨架
   - 判断朝向
   - 显示 8 个 Demo 穴位
   - 实时叠加显示
4. 右侧面板可：
   - 输入患者参数（身高/体重/年龄/性别）
   - 查看处方
   - 查看传感器 Mock 数据
   - 对穴位进行专家修正

## Demo 穴位列表 (v0.1)

| ID | 穴位 | 区域 | 朝向 |
|----|------|------|------|
| GB20 | 风池 | 颈部 | 背面 |
| GB21 | 肩井 | 肩部 | 正面/背面 |
| GV14 | 大椎 | 颈后 | 背面 |
| LI4 | 合谷 | 手部 | 手掌/手背 |
| PC8 | 劳宫 | 手掌 | 手掌 |
| PC6 | 内关 | 前臂 | 正面 |
| ST36 | 足三里 | 小腿 | 正面 |
| SP6 | 三阴交 | 小腿 | 正面 |

## API 文档

启动后端后访问 `http://localhost:8765/docs` 查看 Swagger API 文档。

主要接口：
- `WS /ws/realtime` - 实时视频流 + 穴位推算
- `GET/POST /api/patient/profile` - 患者参数
- `GET /api/acupoints/definitions` - 穴位定义
- `POST /api/expert/correction` - 专家修正
- `GET /api/health` - 健康检查

## 关键设计说明

1. **穴位不是绝对点**：显示为带半径的圆形推荐区域，而非精确点
2. **置信度可视化**：高置信度实线圆（绿），中置信度半透明（黄），低置信度虚线（红）
3. **专家修正可追踪**：保留 AI 原始位置 + 专家修正位置 + 修正原因
4. **穴位定义文件化**：`data/acupoint_definitions/acupoints_v0.1.json`，支持热加载
5. **算法可解释**：每个判断结果附原因列表

## 风险提示

- RGB 单目精度有限，穴位定位仅供参考
- 背面/侧面识别稳定性受光照和遮挡影响
- 手掌/手背判断基于启发式算法，不是深度学习模型
- 本系统**不替代**专业医疗诊断和理疗师判断
