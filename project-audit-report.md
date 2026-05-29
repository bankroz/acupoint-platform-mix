# AI 经络/穴位导航理疗系统 — 项目全面审核报告

> 审核范围：Prompt 覆盖度、架构合理性与解耦、产品化可靠性规划
> 审核时间：2026-05-29
> 审核对象：`prompt.md`、`README.md`、后端 Python 源码（1583 行）、前端 TypeScript 源码（970 行）

---

## 一、Prompt 审核 — 盲区与风险点

### ✅ 已覆盖的核心内容（质量较高）

| 类别 | 覆盖情况 |
|------|----------|
| MVP 技术路线 | ✅ RGB 优先、MediaPipe+YOLOv8、渐进式升级路径清晰 |
| 模块分工 | ✅ 13 个模块边界明确，输入输出格式有样例 |
| 穴位不确定性表达 | ✅ 明确"推荐区域+置信度"而非绝对点 |
| 专家修正可追溯 | ✅ AI 原始点、修正点、修正原因、版本号均有规范 |
| 数据结构规范 | ✅ PatientProfile、AcupointEstimate 等 13 个核心结构有 JSON 示例 |
| 系统定位声明 | ✅ 明确"理疗辅助导航原型，不作独立医疗诊断" |
| 升级路径预留 | ✅ 多相机、深度相机、机械臂接口均有预留数据结构 |

---

### ❌ Prompt 盲区与遗漏问题（共 17 项）

#### 🔴 高优先级盲区（影响系统正确性/安全性）

**B1. 缺少「会话/患者唯一标识」的并发安全说明**
- 现状：Prompt 中 `patient_id` 格式为 `p_001`，但没有规定唯一性生成规则（UUID？自增 ID？）
- 风险：多个理疗师同时操作不同患者时，`_current_patient` 全局状态（已在 `ws/handler.py` 实现为进程级全局变量）会相互覆盖
- 补充建议：每次 WebSocket 连接应绑定独立的 `session_id`，患者状态应随 session 隔离

**B2. 缺少「帧丢弃/降频策略」规范**
- 现状：Prompt 规定了前端每 150ms 抓一帧发送，但没有规定后端处理队列和帧丢弃策略
- 风险：后端 YOLOv8 处理一帧约需 20-80ms（CPU 环境下可能达 200ms+），前端 150ms 发一帧会造成队列堆积，最终 WebSocket 积压导致延迟越来越大
- 补充建议：后端处理完一帧后才发送 ACK，前端收到 ACK 后才发下一帧（背压机制）；或后端明确跳帧逻辑

**B3. 缺少「图像隐私与数据安全」处理规范**
- 现状：系统通过 WebSocket 传输人体图像帧（base64），Prompt 完全未提及数据隐私
- 风险：患者人体图像、理疗处方、穴位修正记录等属于医疗隐私数据，需要加密传输
- 补充建议：明确 WSS 加密传输要求；本地存储的 `corrections/` 和 `sessions/` 是否需要加密；患者数据保存多久/如何删除

**B4. 缺少「系统启动失败处理」规范**
- 现状：若 `yolov8n-pose.pt` 模型文件不存在或 GPU 显存不足，后端 `initialize()` 会抛出异常，整个 FastAPI 进程崩溃
- Prompt 没有说明这种场景下系统应该怎么降级
- 补充建议：模型加载失败时后端应返回有意义的错误状态，前端应展示"后端未就绪"而非静默无响应

**B5. 缺少「专家修正的权限控制」**
- 现状：任何浏览器客户端都可以调用 `POST /api/expert/correction`，没有身份验证
- 风险：恶意用户可以污染专家纠偏数据集（该数据集是未来模型训练的基础）
- 补充建议：专家操作 API 需要 Token 鉴权；correction 记录中的 `expert_id` 需要来自认证系统而非客户端自填

---

#### 🟡 中优先级盲区（影响产品稳定性）

**B6. 缺少「处方版本化」规范**
- 现状：穴位定义文件（acupoints）有版本号管理，但处方（Prescription）没有版本字段
- 风险：医生修改处方后，正在执行的理疗过程会静默使用新版本，历史记录与处方不可对应
- 补充建议：`Prescription` 增加 `version` 字段，专家修正记录中需要关联 `prescription_version`

**B7. 缺少「多人场景」（多目标）的处理规范**
- 现状：Prompt 在 Module 2（姿态估计）提到"支持多人时选择主目标"，但没有规定主目标选择规则
- 风险：两人同时进入画面时，系统会随机选错主目标（患者 vs 理疗师），穴位标注跑偏
- 补充建议：明确主目标选择规则（画面中心优先？最大包围框优先？手动锁定？）

**B8. 缺少「穴位定义文件热加载的幂等性」规范**
- 现状：提供了 `POST /api/acupoints/definitions/reload` 接口，但若热加载时正在进行姿态估计会出现竞态条件
- 补充建议：热加载应有锁机制，加载期间的帧处理使用旧版本定义；加载完成后新帧使用新版本

**B9. 缺少「同身寸估算的置信度聚合策略」说明**
- 现状：Module 8 定义了多种同身寸来源，但没有说明当多个来源的 cun_px 差异过大时如何处理
- 补充建议：当不同方法估算差异超过 15% 时，应显式警告"同身寸估算不一致，建议专家校准"

**B10. 缺少「穴位定义文件格式校验」**
- 现状：`POST /api/acupoints/definitions/reload` 直接加载 JSON，没有说明如何校验格式合法性
- 风险：加载格式错误的穴位文件会导致运行时异常
- 补充建议：使用 Pydantic 对穴位 JSON 文件做 schema 校验，验证失败时保留旧版本并返回错误详情

**B11. 缺少「浏览器兼容性要求」**
- 现状：前端使用 WebRTC (`getUserMedia`) 和 WebSocket，但没有规定浏览器版本要求
- 风险：Safari 对 WebRTC 的权限策略与 Chrome 不同；旧版 iOS Safari 不支持某些 `MediaDevices` API
- 补充建议：明确支持的浏览器矩阵（Chrome ≥ 90、Firefox ≥ 85、Edge ≥ 90，不支持 IE）

---

#### 🟢 低优先级盲区（影响可维护性/未来升级）

**B12. 缺少「算法版本与穴位定义版本的兼容性矩阵」**
- 专家修正记录中保存了 `algorithm_version` 和 `acupoint_definition_version`，但没有规定不同版本组合的兼容性策略
- 未来模型升级后，旧版修正数据是否仍有效？

**B13. 缺少「骨架关键点坐标系归一化说明」**
- YOLOv8 输出的是图像归一化坐标（0~1），MediaPipe 也是归一化坐标，但二者的坐标原点定义是否完全一致未说明
- 混用时可能出现微小偏差，在穴位定位精度要求高时会累积误差

**B14. 缺少「数据导出格式标准」**
- Prompt 说"数据应可导出为 JSON/CSV"，但没有定义导出文件的具体 schema 和命名规范
- 未来需要用这些数据训练模型，格式不规范会增加数据清洗成本

**B15. 缺少「本地模式（离线模式）」支持说明**
- 系统依赖摄像头+后端服务，没有说明后端不可用时前端的降级行为
- 补充建议：至少有明确的"连接中断"提示，防止用户误以为系统在正常工作

**B16. 缺少「系统性能指标基线」**
- Prompt 没有规定端到端延迟要求（摄像头帧 → 穴位叠加显示）
- 没有规定最低帧率要求（5fps？10fps？）
- 没有目标设备配置要求（CPU 最低配置）

**B17. 缺少「穴位标注文件的来源与医学合规性」说明**
- 当前穴位定义完全由开发者手工编写（`"source": "internal_rule_based_definition"`），没有规定数据核实流程
- 建议：明确穴位定义需要中医执业医师审核，并在文件中记录审核人信息

---

## 二、架构审核 — 合理性评估与解耦规划

### 2.1 README 描述的框架评估

README 描述的框架（YOLOv8-Pose + MediaPipe Hands + FastAPI + React/Zustand）与 Prompt 规划的框架（MediaPipe Holistic + FastAPI + React）存在**一个已落地的合理偏差**：

| 对比项 | Prompt 推荐 | README/实际使用 | 评估 |
|--------|-------------|-----------------|------|
| 身体姿态估计 | MediaPipe Holistic | **YOLOv8-Pose** | ✅ 合理升级：YOLOv8 在人体检测稳定性上优于 MediaPipe |
| 手部关键点 | MediaPipe Hands（内含于 Holistic）| **MediaPipe Hands（独立）** | ✅ 合理拆分 |
| 前端状态管理 | Zustand 或 Redux | **Zustand** | ✅ 合理选择 |
| 数据库 | SQLite/PostgreSQL | **JSON 文件（corrections/）** | ⚠️ MVP 阶段可接受，产品化前需升级 |
| WebSocket | FastAPI WebSocket | ✅ 已实现 | ✅ 符合规划 |

**整体评估：README 描述的框架分配是合理的，实际开发没有明显偏离设计原则。**

---

### 2.2 当前架构中的问题与解耦规划

#### 后端解耦工作

---

**[解耦-B1] 提取共用工具函数 `_get_kp` 到 `modules/utils.py`**

**问题：** `_get_kp()` 在 3 个模块中完全重复定义：
- `modules/acupoint_estimator.py` 第 23 行
- `modules/cun_measurement.py` 第 15 行
- `modules/body_orientation.py` 第 13 行

**解耦方案：**
```
新建 backend/modules/utils.py
  ├── get_keypoint_by_name(result, name) → Optional[BodyKeypoint]
  ├── get_hand_landmark_by_name(hand, name) → Optional[HandKeypoint]
  └── get_hand_by_id(result, hand_id) → Optional[HandLandmarks]
```

以上三个函数同时也在 `PoseEstimator` 类中以实例方法的形式存在，可统一归入 `utils.py` 后删除 `PoseEstimator` 中的重复实现。

---

**[解耦-B2] 拆分 `ws/handler.py` 中业务逻辑与 WebSocket 通信**

**问题：** `ws/handler.py` 同时承担：
1. WebSocket 消息路由（通信层）
2. 全局会话状态管理（`_current_patient`, `_current_definitions`, `_expert_corrections`）
3. 帧处理编排（调用姿态估计 → 穴位推算）
4. 响应序列化（`_encode_response`）

`main.py` 的 REST 路由通过惰性导入调用 `handler.py` 中的状态管理函数，产生了 REST API 对 WebSocket 层的依赖倒置。

**解耦方案：**
```
新建 backend/services/session_service.py  ← 会话状态管理（独立于 WS）
  ├── get_current_patient()
  ├── update_patient(patient)
  ├── reload_definitions()
  └── get_current_definitions()

重构 backend/ws/handler.py  ← 只保留 WS 通信逻辑
  ├── _decode_frame()
  ├── _encode_response()    ← 改用 model.model_dump() 替换手工序列化
  └── ws_handler()           ← 消息路由，委托给 session_service

更新 backend/main.py  ← REST 路由直接依赖 session_service，不再依赖 ws.handler
```

---

**[解耦-B3] 拆分 `modules/acupoint_estimator.py` 中的 `_compute_acupoint_position`**

**问题：** `_compute_acupoint_position` 函数 165 行，承担了朝向检查、规则执行、参数修正、半径计算四个职责。

**解耦方案（内部重构，不改公共 API）：**
```python
# 拆分为 4 个私有函数
def _check_visibility(acupoint_def, body_orient, hand_orient) → tuple[bool, str]
def _apply_landmark_rule(rule, pose_result, cun_result, factors) → Optional[tuple[float, float]]
def _apply_patient_correction(x, y, factors) → tuple[float, float]
def _compute_radius(acupoint_def, factors) → float

# 原 _compute_acupoint_position 变为编排函数（约 30 行）
def _compute_acupoint_position(...) → Optional[AcupointEstimate]:
    valid, reason = _check_visibility(...)
    pos = _apply_landmark_rule(...)
    corrected_pos = _apply_patient_correction(...)
    radius = _compute_radius(...)
    return AcupointEstimate(...)
```

---

**[解耦-B4] 修复 `ws/handler.py` 中 `_encode_response` 手工序列化**

**问题：** 73 行手工字段映射，每次改 Pydantic 模型都需同步维护。

**修复方案：**
```python
def _encode_response(result: PoseResult, acupoint_result: AcupointResult) -> dict:
    # 在序列化前应用内存中的专家修正
    acupoint_dict = acupoint_result.model_dump()
    for ap in acupoint_dict.get("acupoints", []):
        if ap["id"] in _expert_corrections:
            ap.update(_expert_corrections[ap["id"]])
    return {
        "type": "result",
        "timestamp": time.time(),
        "pose": result.model_dump(),
        "acupoint_result": acupoint_dict,
    }
```

---

**[解耦-B5] 修复 `main.py` 中 CORS 配置死代码**

**问题：** `config.py` 中 `CORS_ORIGINS` 有意义的白名单从未被使用，实际使用了 `allow_origins=["*"]`（同时设置 `allow_credentials=True` 会导致浏览器 CORS 错误）。

**修复方案：**
```python
# main.py 第 29 行
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,  # 从 config 读取
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

**[解耦-B6] 修复 `schemas/models.py` 中 `PatientProfile` 的 `__init__` 覆写**

**问题：** 重写 `__init__` 会绕过 Pydantic v2 部分验证机制。

**修复方案：**
```python
from pydantic import model_validator

class PatientProfile(BaseModel):
    # ... 字段定义不变 ...
    
    @model_validator(mode='after')
    def compute_bmi_and_type(self) -> 'PatientProfile':
        if self.bmi is None and self.height_cm > 0 and self.weight_kg > 0:
            h = self.height_cm / 100
            self.bmi = round(self.weight_kg / (h * h), 1)
        if self.body_type == 'normal' and self.bmi is not None:
            # ... body_type 分类逻辑不变 ...
        return self
```

---

#### 前端解耦工作

---

**[解耦-F1] 拆分 `OverlayCanvas.tsx` 中的 258 行单一 `useEffect`**

**问题：** 7 个绘制阶段串行写在一个 effect 里，无法独立关闭/调试某一层，`handConnections` 常量每次 effect 内重建。

**解耦方案：**
```typescript
// 新建 frontend/src/utils/canvas-renderers.ts
export function drawSkeleton(ctx, keypoints, skeletonPairs) {...}
export function drawHandKeypoints(ctx, handData, handConnections) {...}
export function drawMeridians(ctx, keypoints, meridianPairs) {...}
export function drawAcupoints(ctx, acupoints, corrections) {...}
export function drawOrientationLabels(ctx, bodyOrient, handOrient) {...}
export function drawStatusHints(ctx, result) {...}

// 常量移到文件顶层（只定义一次）
const SKELETON_PAIRS = [...] // 已在文件顶层，保持不变
const HAND_CONNECTIONS = [...]  // 从 useEffect 内部移出
const MERIDIAN_PAIRS = [...]    // 已在文件顶层，保持不变

// OverlayCanvas.tsx 的 useEffect 简化为约 30 行的编排调用
useEffect(() => {
    if (!canvasRef.current || !result) return;
    const ctx = canvasRef.current.getContext('2d');
    ctx.clearRect(0, 0, width, height);
    drawSkeleton(ctx, result.pose.body_keypoints, SKELETON_PAIRS);
    drawHandKeypoints(ctx, result.pose.hands, HAND_CONNECTIONS);
    drawMeridians(ctx, result.pose.body_keypoints, MERIDIAN_PAIRS);
    drawAcupoints(ctx, result.acupoint_result.acupoints, expertCorrections);
    drawOrientationLabels(ctx, result.pose.body_orientation, result.pose.hand_orientations);
    drawStatusHints(ctx, result);
}, [result, width, height, expertCorrections]);
```

---

**[解耦-F2] 修复 `useWebSocket.ts` 多组件实例化问题（静默发送失败）**

**问题：** `ExpertPanel` 和 `PatientPanel` 各自调用 `useWebSocket()`，但只有 `CameraView` 调用了 `connect()`，所以前两者的 `wsRef.current === null`，发送操作静默失败。

**解耦方案：将 WebSocket 实例提升到 Zustand store 或 Context**
```typescript
// 方案A：提升到 appStore
// frontend/src/store/appStore.ts 增加
wsRef: React.MutableRefObject<WebSocket | null>;

// 方案B（推荐）：提升到 Context
// frontend/src/contexts/WebSocketContext.tsx
const WebSocketContext = createContext<WebSocketAPI>(null);
export const WebSocketProvider = ({ children }) => {
    const wsRef = useRef<WebSocket | null>(null);
    // connect / disconnect / send* 方法只在此定义
    return <WebSocketContext.Provider value={{...}}>{children}</WebSocketContext.Provider>
};
// 所有组件通过 useContext(WebSocketContext) 获取同一个 WS 实例
```

---

**[解耦-F3] 修复 `useCamera.ts` 高频临时 canvas 创建**

```typescript
// useCamera.ts 内部添加离屏 canvas 引用
const offscreenCanvasRef = useRef<HTMLCanvasElement | null>(null);

// captureFrame 改为复用离屏 canvas
const captureFrame = useCallback(() => {
    const video = videoRef.current;
    if (!video || video.readyState < 2) return null;
    if (!offscreenCanvasRef.current) {
        offscreenCanvasRef.current = document.createElement('canvas');
    }
    const canvas = offscreenCanvasRef.current;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d')!.drawImage(video, 0, 0);
    return canvas.toDataURL('image/jpeg', 0.7);
}, []);
```

---

**[解耦-F4] 修复 `useWebSocket.ts` 自动重连闭包陷阱**

**问题：** `onclose` 内直接捕获旧版 `connect` 函数引用。

```typescript
// 使用 useRef 持有稳定引用
const connectRef = useRef<() => void>(null!);
connectRef.current = connect;  // 每次渲染同步更新

// onclose 使用 ref 调用
ws.onclose = () => {
    setWsConnected(false);
    setTimeout(() => connectRef.current?.(), 3000);  // 总是调用最新版 connect
};
```

---

### 2.3 解耦优先级汇总表

| 编号 | 文件 | 问题描述 | 优先级 | 工作量 |
|------|------|----------|--------|--------|
| 解耦-B1 | `modules/utils.py`（新建）| `_get_kp` 三处重复 | 🟡 中 | 0.5h |
| 解耦-B2 | `ws/handler.py` + `services/session_service.py` | 业务逻辑混入 WS 层 | 🔴 高 | 3h |
| 解耦-B3 | `modules/acupoint_estimator.py` | 165 行单函数拆分 | 🟡 中 | 2h |
| 解耦-B4 | `ws/handler.py` `_encode_response` | 手工序列化替换 | 🟡 中 | 1h |
| 解耦-B5 | `main.py` CORS 配置 | 死代码修复 | 🟢 低 | 0.25h |
| 解耦-B6 | `schemas/models.py` `PatientProfile` | Pydantic v2 validator | 🟢 低 | 0.5h |
| 解耦-F1 | `OverlayCanvas.tsx` | 258 行 useEffect 拆分 | 🔴 高 | 3h |
| 解耦-F2 | `useWebSocket.ts` + Context | 多实例静默失败 | 🔴 高 | 2h |
| 解耦-F3 | `useCamera.ts` `captureFrame` | 高频 canvas 创建 | 🟡 中 | 0.5h |
| 解耦-F4 | `useWebSocket.ts` | 重连闭包陷阱 | 🟡 中 | 0.5h |

---

## 三、产品化可靠性风险规划

> 以下为产品化过程中必须解决的可靠性问题，按类别分组，每项包含：风险描述、触发条件、建议方案、实施位置。

---

### 3.1 弱网与网络波动

#### R1. WebSocket 帧积压导致延迟雪崩

**风险描述：** 后端处理速度（40~200ms/帧）低于前端发送频率（150ms/帧），帧会在 WebSocket 缓冲区积压，最终延迟越来越大，体验接近"幻灯片模式"。

**触发条件：** CPU 机器运行 YOLOv8；网络延迟 > 50ms；多路摄像头并发。

**建议方案：**
```
前端实现「背压控制」：
  - 前端维护一个 pendingFrame 布尔锁
  - 发送帧后将锁设为 true，等收到后端 result 消息再解锁
  - 解锁后才发下一帧

后端实现「帧跳过」：
  - 后端 WebSocket handler 检查队列深度
  - 若当前正在处理，直接 discard 新到的帧，发送 { type: 'skip', frame_id: xxx }
  - 前端收到 skip 消息后解锁，继续发下一帧
```

**实施位置：** `useWebSocket.ts`（前端锁）、`ws/handler.py`（后端队列判断）

---

#### R2. WebSocket 断线重连期间的专家修正丢失

**风险描述：** 专家正在拖拽修正穴位时 WebSocket 断线，`sendExpertCorrection()` 调用 `wsRef.current` 为 null，修正数据静默丢弃。

**建议方案：**
```
前端实现「发送队列」：
  - useWebSocket 维护 pendingMessages: Message[]
  - ws 断开时，发送操作 push 到队列而非丢弃
  - 重连成功后（onopen），flush 队列逐条发送

关键操作降级为 REST：
  - 专家修正在 WS 不可用时降级为 POST /api/expert/correction
  - 该 REST 接口已存在（correction_store.save_correction），直接利用
```

**实施位置：** `useWebSocket.ts`（消息队列）、`ExpertPanel.tsx`（降级发送逻辑）

---

#### R3. 弱网下 base64 帧压缩率不足

**风险描述：** 当前 `captureFrame` 用 JPEG quality=0.7，1280×720 图像约 80~150KB，弱网（< 2Mbps）下会造成明显延迟。

**建议方案：**
```
动态质量调整：
  - 前端维护 lastRTT（round-trip time）估算：发送时间戳 → 收到 result 时计算 RTT
  - RTT < 200ms: quality=0.7, 无跳帧
  - RTT 200~500ms: quality=0.5, 帧率降至 5fps（每 200ms 发一帧）
  - RTT > 500ms: quality=0.3, 帧率降至 2fps

分辨率自适应：
  - 640×480 in 弱网模式（已足够骨架识别）
  - 320×240 in 极弱网模式（仅供朝向判断）
```

**实施位置：** `useCamera.ts` `captureFrame`、`useWebSocket.ts` RTT 计算

---

### 3.2 幂等性与数据一致性

#### R4. 专家修正重复提交

**风险描述：** 网络超时导致用户重复点击保存，同一修正操作被写入两次，污染训练数据集。

**建议方案：**
```
前端：防重复提交
  - 提交后立即 disable 保存按钮，直到收到确认响应
  - 每次修正生成客户端唯一 correction_id（UUID）随数据一同提交

后端：幂等处理
  - correction_store 写入前检查 correction_id 是否已存在
  - 若存在，返回 200 + 原记录（而非 409 错误），让客户端静默通过
```

**实施位置：** `ExpertPanel.tsx`（UUID + 禁用逻辑）、`correction_store.py`（幂等检查）

---

#### R5. 穴位定义热加载与并发帧处理的竞态

**风险描述：** `POST /api/acupoints/definitions/reload` 触发热加载时，若有帧正在使用旧定义处理中（`estimate_acupoints` 正在执行），会出现新旧定义混用的情况，可能导致穴位 ID 对应关系错误。

**建议方案：**
```python
# ws/handler.py 中使用读写锁（asyncio.Lock）
_definition_lock = asyncio.Lock()

async def reload_definitions():
    async with _definition_lock:
        _current_definitions = load_acupoint_definitions()

# ws_handler 中处理帧前加读锁
async def ws_handler(ws):
    async with _definition_lock:
        defs = _current_definitions  # 获取快照
    result = await estimate_acupoints(frame, defs, ...)
```

**实施位置：** `ws/handler.py`（异步锁）、`main.py` reload 路由

---

#### R6. 患者参数更新与当前帧处理的竞态

**风险描述：** 理疗师在理疗中途修改患者参数（如输入新身高），参数修正因子在计算到一半时被替换，穴位位置出现跳变。

**建议方案：**
```
每次帧处理开始时，快照当前患者参数：
  patient_snapshot = copy.deepcopy(_current_patient)
  使用 patient_snapshot 完成整帧的穴位推算
  不要在帧处理过程中读取全局 _current_patient
```

**实施位置：** `ws/handler.py` `ws_handler` 函数帧处理入口

---

### 3.3 断线与会话恢复

#### R7. 长时间治疗会话中 WebSocket 被服务端超时关闭

**风险描述：** 理疗过程可能持续 30~60 分钟，网关（Nginx/负载均衡器）默认 WebSocket idle timeout 约 60 秒，会主动断开空闲连接。

**建议方案：**
```
客户端心跳：
  - 已有 ping 消息类型（handler.py 第 219 行已处理）
  - 前端每 30 秒发送 { type: 'ping' }，后端回复 { type: 'pong' }
  - 60 秒未收到 pong，触发重连

后端配置：
  - uvicorn 添加 ws_ping_interval=20, ws_ping_timeout=30
  - 若使用 Nginx 代理，需设置 proxy_read_timeout 300s
```

**实施位置：** `useWebSocket.ts`（心跳 interval）、`ws/handler.py`（pong 处理）、部署配置

---

#### R8. 后端重启后前端会话状态丢失

**风险描述：** 后端重启（更新代码、崩溃恢复）后，`_current_patient` 和 `_expert_corrections` 内存状态全部清空，前端界面的患者参数无法恢复。

**建议方案：**
```
短期（MVP 阶段）：
  - 患者参数在前端 localStorage 持久化（已有 Zustand store）
  - 重连成功后，前端自动发送 patient_update 恢复后端状态

中期：
  - 后端引入 SQLite 存储患者参数和会话状态
  - 使用 session_id 关联，重连时 client 携带 session_id，后端恢复该 session 的状态

实施位置：
  - appStore.ts（persist middleware）
  - useWebSocket.ts onopen（重连后自动发 patient_update）
```

---

#### R9. 摄像头权限被用户中途撤销

**风险描述：** 用户在 Chrome 权限设置中撤销摄像头权限，`MediaStream` 的 track 会触发 `ended` 事件，但当前代码没有监听这个事件。

**建议方案：**
```typescript
// useCamera.ts 中添加
stream.getVideoTracks()[0].addEventListener('ended', () => {
    setError('摄像头访问权限已被撤销，请刷新页面重新授权');
    setActive(false);
    setCameraActive(false);
    disconnect();  // 同步断开 WebSocket
});
```

**实施位置：** `useCamera.ts` `start()` 函数

---

### 3.4 网络攻击与安全加固

#### R10. WebSocket 接口无鉴权，可被任意客户端滥用

**风险描述：** `WS /ws/realtime` 接口完全开放，攻击者可以：
1. 发送大量视频帧耗尽服务器 CPU（DoS）
2. 发送伪造的 `expert_correction` 污染训练数据
3. 获取系统的穴位推算结果和患者数据

**建议方案：**
```
第一阶段（Token 鉴权）：
  - 前端连接时在 URL 中携带 token：wss://host/ws/realtime?token=xxx
  - 后端握手时验证 token（可用简单的 HMAC-SHA256 签名，不依赖数据库）
  - 无效 token 立即关闭连接

第二阶段（速率限制）：
  - 每个 WebSocket 连接的帧处理速率限制（最多 10fps，超出直接丢弃）
  - 全局并发连接数限制（生产环境限制 N 个并发，避免资源耗尽）
```

**实施位置：** `ws/handler.py` 握手验证、`main.py` 限流中间件

---

#### R11. base64 图像注入攻击

**风险描述：** 前端发送的 base64 帧在后端 `_decode_frame` 中 `base64.b64decode` + `cv2.imdecode`，恶意构造的畸形二进制数据可能触发 OpenCV 的图像解码漏洞（历史上 OpenCV 有多个 CVE）。

**建议方案：**
```python
def _decode_frame(data: str) -> Optional[np.ndarray]:
    try:
        # 1. 长度限制（防止超大 payload）
        if len(data) > 2 * 1024 * 1024:  # 2MB base64 上限
            logger.warning("Frame too large, discarded")
            return None
        
        # 2. 前缀校验（只允许合法的 JPEG/PNG data URL）
        if not data.startswith('data:image/'):
            return None
        
        # 3. 解码
        raw = base64.b64decode(data.split(',')[1])
        
        # 4. 文件头魔数校验（JPEG: ff d8 ff，PNG: 89 50 4e 47）
        if not (raw[:2] == b'\xff\xd8' or raw[:4] == b'\x89PNG'):
            return None
        
        arr = np.frombuffer(raw, np.uint8)
        return cv2.imdecode(arr, cv2.IMREAD_COLOR)
    except Exception:
        return None
```

**实施位置：** `ws/handler.py` `_decode_frame`

---

#### R12. REST API 缺少输入大小限制

**风险描述：** `POST /api/patient/profile`、`POST /api/expert/correction` 等接口没有请求体大小限制，攻击者可发送超大请求体占用内存。

**建议方案：**
```python
# main.py 添加请求体大小限制中间件
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware

class LimitUploadSize(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.headers.get("content-length"):
            if int(request.headers["content-length"]) > 1024 * 1024:  # 1MB 限制
                return Response("Request too large", status_code=413)
        return await call_next(request)

app.add_middleware(LimitUploadSize)
```

**实施位置：** `main.py`

---

#### R13. 患者数据未加密存储

**风险描述：** `data/corrections/`、`data/sessions/` 下的 JSON 文件包含患者 ID、身高、体重、年龄、穴位修正记录等，明文存储在文件系统中，不符合医疗数据隐私合规（HIPAA/国内医疗数据管理规范）。

**建议方案：**
```
近期措施：
  - 本地 JSON 文件存储前，对患者敏感字段（height_cm, weight_kg, age, sex）进行对称加密（AES-256-GCM）
  - 加密密钥通过环境变量传入，不硬编码

中期措施：
  - 迁移到 SQLite，开启 SQLCipher 加密
  - 患者文件访问需要操作系统级别的权限控制

远期措施（商业化）：
  - 评估 GDPR/国内《个人信息保护法》合规要求
  - 实现数据保留策略（自动删除 N 天前的记录）
  - 实现患者数据删除（删除权）
```

**实施位置：** `correction_store.py`（加密写入/解密读取）

---

#### R14. 缺少操作审计日志

**风险描述：** 谁在什么时间修改了患者参数、谁提交了哪条专家修正，目前只有修正记录本身，没有操作级别的审计日志。

**建议方案：**
```python
# 新建 backend/services/audit_log.py
def log_action(action: str, operator_id: str, patient_id: str, detail: dict):
    entry = {
        "ts": datetime.utcnow().isoformat(),
        "action": action,       # e.g. "expert_correction", "patient_update"
        "operator_id": operator_id,
        "patient_id": patient_id,
        "detail": detail,
        "ip": ...               # 从请求上下文获取
    }
    # 写入审计日志文件（独立于业务数据）
```

**实施位置：** 新建 `services/audit_log.py`，在 `save_correction`、`update_patient` 中调用

---

### 3.5 其他可靠性风险

#### R15. 后端未实现健康检查的深度监控

**风险描述：** `GET /api/health` 当前只返回 `{"status": "ok"}`，不检查 YOLO 模型是否加载成功、MediaPipe 是否可用、文件系统是否可写。

**建议方案：**
```python
@app.get("/api/health")
async def health_check():
    from ws.handler import pose_engine
    return {
        "status": "ok",
        "yolo_ready": pose_engine._yolo is not None,
        "mediapipe_ready": pose_engine._hand_available,
        "definitions_loaded": _current_definitions is not None,
        "definitions_count": len(_current_definitions.acupoints) if _current_definitions else 0,
        "corrections_dir_writable": os.access(CORRECTIONS_DIR, os.W_OK),
        "timestamp": time.time()
    }
```

---

#### R16. 无限制的专家修正文件增长

**风险描述：** 每次专家修正追加写入 JSON 文件，长期使用后文件无限增长，读取时全文件解析性能下降。

**建议方案：**
```
近期：
  - correction_store.save_correction 中检查文件大小，超过 10MB 时触发归档
  - 旧文件重命名为 corrections_YYYYMM.json，新文件继续写

中期：
  - 迁移到 SQLite + 索引，支持高效按 patient_id/acupoint_id/timestamp 查询
```

---

#### R17. 前端无「摄像头权限被拒」的优雅处理

**风险描述：** 用户点击「开启摄像头」后浏览器弹出权限请求，若用户点拒绝，`getUserMedia` 抛出 `NotAllowedError`，当前 `useCamera.ts` 已有 `setError`，但错误消息不够用户友好。

**建议方案：**
```typescript
// useCamera.ts start() 的 catch 块
} catch (err: any) {
    const msgs: Record<string, string> = {
        'NotAllowedError': '摄像头访问被拒绝，请在浏览器地址栏点击摄像头图标重新授权',
        'NotFoundError': '未检测到摄像头设备，请确认已连接并被系统识别',
        'NotReadableError': '摄像头被其他程序占用，请关闭其他视频应用后重试',
        'OverconstrainedError': '摄像头不支持所需分辨率，请尝试其他摄像头',
    };
    setError(msgs[err.name] ?? `摄像头错误：${err.message}`);
}
```

---

### 3.6 可靠性风险优先级汇总

| 编号 | 类别 | 风险描述 | 优先级 | 阶段 |
|------|------|----------|--------|------|
| R1 | 弱网 | WebSocket 帧积压/延迟雪崩 | 🔴 高 | MVP 前必解决 |
| R2 | 断线 | 专家修正断线丢失 | 🔴 高 | MVP 前必解决 |
| R10 | 安全 | WS 接口无鉴权 | 🔴 高 | 产品化前必解决 |
| R11 | 安全 | base64 图像注入 | 🔴 高 | 产品化前必解决 |
| R4 | 幂等 | 专家修正重复提交 | 🟡 中 | Sprint 4 |
| R5 | 幂等 | 热加载竞态条件 | 🟡 中 | Sprint 4 |
| R6 | 幂等 | 患者参数更新竞态 | 🟡 中 | Sprint 4 |
| R7 | 断线 | WS 超时被网关关闭 | 🟡 中 | 部署前 |
| R8 | 断线 | 后端重启会话丢失 | 🟡 中 | 产品化前 |
| R3 | 弱网 | 弱网帧压缩率不足 | 🟡 中 | 性能优化阶段 |
| R12 | 安全 | REST 接口无大小限制 | 🟡 中 | 产品化前 |
| R13 | 安全 | 患者数据未加密 | 🟡 中 | 合规化前 |
| R9 | 断线 | 摄像头权限中途撤销 | 🟢 低 | Sprint 5 |
| R14 | 安全 | 缺少审计日志 | 🟢 低 | 商业化前 |
| R15 | 可靠性 | 健康检查不完整 | 🟢 低 | 运维接入前 |
| R16 | 可靠性 | 修正文件无限增长 | 🟢 低 | 数据量增长后 |
| R17 | 可靠性 | 摄像头权限拒绝提示 | 🟢 低 | 体验优化阶段 |

---

## 四、执行路线图建议

### Sprint 4.5（紧急修复，建议 1 周内）
1. 解耦-F2：修复 WebSocket 多实例静默失败（专家修正实际发不出去）
2. R10：为 WS 接口添加基础 Token 鉴权
3. R11：`_decode_frame` 添加大小限制和魔数校验
4. 解耦-B5：修复 CORS 配置死代码（`allow_origins=["*"]` 会引发生产浏览器报错）

### Sprint 5（产品化基础，2 周）
1. 解耦-B2：`session_service.py` 独立会话状态
2. 解耦-F1：`OverlayCanvas` 渲染函数拆分
3. R1：实现帧发送背压控制
4. R2：专家修正发送队列 + REST 降级
5. R4：修正幂等性（UUID + 防重复提交）
6. R8：Zustand persist + 重连后自动恢复患者参数

### Sprint 6（稳定性与合规，3 周）
1. R3：弱网自适应压缩率
2. R5/R6：热加载和患者参数竞态锁
3. R7：心跳保活机制完善
4. R13：患者敏感字段加密存储
5. B1～B5：Prompt 高优先级盲区对应的功能补全（session 隔离、背压说明、隐私数据处理规范）

---

*报告由 AI 审核生成，建议由开发者结合项目实际情况调整优先级后执行。*
