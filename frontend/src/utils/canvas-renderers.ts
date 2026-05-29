/**
 * Canvas 渲染工具函数 — 从 OverlayCanvas.tsx 拆出，便于独立测试和复用。
 *
 * 解耦-F1：将 300+ 行的单一 useEffect 拆分为 6 个独立渲染函数。
 * 每个函数职责单一，可单独关闭/调试，常量提到文件顶层只定义一次。
 */

import type { WSResult, BodyKeypoint, HandData } from '../types';

// ============================================================
// 常量（从 useEffect 内部提到文件顶层）
// ============================================================

export const SKELETON_PAIRS: [string, string][] = [
  ['nose', 'left_eye'], ['nose', 'right_eye'],
  ['left_eye', 'left_ear'], ['right_eye', 'right_ear'],
  ['left_shoulder', 'right_shoulder'],
  ['left_shoulder', 'left_elbow'], ['left_elbow', 'left_wrist'],
  ['right_shoulder', 'right_elbow'], ['right_elbow', 'right_wrist'],
  ['left_shoulder', 'left_hip'], ['right_shoulder', 'right_hip'],
  ['left_hip', 'right_hip'],
  ['left_hip', 'left_knee'], ['left_knee', 'left_ankle'],
  ['right_hip', 'right_knee'], ['right_knee', 'right_ankle'],
];

export const HAND_CONNECTIONS: [number, number][] = [
  [0, 1], [1, 2], [2, 3], [3, 4],
  [0, 5], [5, 6], [6, 7], [7, 8],
  [0, 9], [9, 10], [10, 11], [11, 12],
  [0, 13], [13, 14], [14, 15], [15, 16],
  [0, 17], [17, 18], [18, 19], [19, 20],
  [5, 9], [9, 13], [13, 17],
];

export const MERIDIAN_PAIRS: [string, string][] = [
  ['left_shoulder', 'left_elbow'],
  ['left_elbow', 'left_wrist'],
  ['right_shoulder', 'right_elbow'],
  ['right_elbow', 'right_wrist'],
];

const ORIENT_LABELS: Record<string, string> = {
  front: '正面', back: '背面', left_side: '左侧', right_side: '右侧',
  partial_front: '部分正面', unknown: '未知',
};

const FACE_ACUPOINT_IDS = new Set(['EX-HN3', 'EX-HN5', 'LI20', 'ST2']);
const HAND_ACUPOINT_IDS = new Set(['LI4', 'PC8', 'PC6']);

// ============================================================
// 渲染函数
// ============================================================

interface DrawContext {
  ctx: CanvasRenderingContext2D;
  width: number;
  height: number;
  isOffline: boolean;
}

/** 步骤 1 — 绘制身体骨架线 */
export function drawSkeleton(
  ctx: CanvasRenderingContext2D,
  keypoints: BodyKeypoint[],
  width: number,
  height: number,
) {
  const kpMap = new Map<string, BodyKeypoint>();
  keypoints.forEach((kp) => kpMap.set(kp.name, kp));

  ctx.strokeStyle = 'rgba(0, 255, 0, 0.6)';
  ctx.lineWidth = 2;

  for (const [a, b] of SKELETON_PAIRS) {
    const ka = kpMap.get(a);
    const kb = kpMap.get(b);
    if (ka && kb && ka.confidence > 0.3 && kb.confidence > 0.3) {
      ctx.beginPath();
      ctx.moveTo(ka.x * width, ka.y * height);
      ctx.lineTo(kb.x * width, kb.y * height);
      ctx.stroke();
    }
  }

  // 关键点圆点
  keypoints.forEach((kp) => {
    if (kp.confidence < 0.3) return;
    const x = kp.x * width;
    const y = kp.y * height;
    const alpha = Math.min(kp.confidence + 0.3, 1);

    ctx.beginPath();
    ctx.arc(x, y, 5, 0, Math.PI * 2);
    ctx.fillStyle = `rgba(0, 255, 100, ${alpha})`;
    ctx.fill();
    ctx.strokeStyle = `rgba(255, 255, 255, ${alpha})`;
    ctx.lineWidth = 1;
    ctx.stroke();
  });
}

/** 步骤 2 — 绘制手部关键点 */
export function drawHandKeypoints(
  ctx: CanvasRenderingContext2D,
  hands: HandData[],
  width: number,
  height: number,
) {
  for (const hand of hands) {
    if (!hand.landmarks || hand.landmarks.length < 21) continue;

    // 手部骨架线
    ctx.strokeStyle = 'rgba(255, 165, 0, 0.5)';
    ctx.lineWidth = 1.5;
    for (const [ai, bi] of HAND_CONNECTIONS) {
      if (ai < hand.landmarks.length && bi < hand.landmarks.length) {
        const la = hand.landmarks[ai];
        const lb = hand.landmarks[bi];
        ctx.beginPath();
        ctx.moveTo(la.x * width, la.y * height);
        ctx.lineTo(lb.x * width, lb.y * height);
        ctx.stroke();
      }
    }

    // 手部关键点
    hand.landmarks.slice(0, 21).forEach((lm: {x: number; y: number}) => {
      ctx.beginPath();
      ctx.arc(lm.x * width, lm.y * height, 3, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(255, 165, 0, 0.8)';
      ctx.fill();
    });
  }
}

/** 步骤 3 — 绘制经络线 */
export function drawMeridians(
  ctx: CanvasRenderingContext2D,
  keypoints: BodyKeypoint[],
  width: number,
  height: number,
) {
  const kpMap = new Map<string, BodyKeypoint>();
  keypoints.forEach((kp) => kpMap.set(kp.name, kp));

  ctx.strokeStyle = 'rgba(0, 200, 200, 0.4)';
  ctx.lineWidth = 2;
  ctx.setLineDash([8, 4]);

  for (const [a, b] of MERIDIAN_PAIRS) {
    const ka = kpMap.get(a);
    const kb = kpMap.get(b);
    if (ka && kb && ka.confidence > 0.3 && kb.confidence > 0.3) {
      ctx.beginPath();
      ctx.moveTo(ka.x * width, ka.y * height);
      ctx.lineTo(kb.x * width, kb.y * height);
      ctx.stroke();
    }
  }

  ctx.setLineDash([]);
}

/** 步骤 4 — 绘制穴位标注 */
export function drawAcupoints(
  ctx: CanvasRenderingContext2D,
  acupoints: any[],
  width: number,
  height: number,
  isOffline: boolean,
) {
  for (const acu of acupoints) {
    if (!acu.visible || acu.x == null || acu.y == null) continue;

    const ax = acu.x * width;
    const ay = acu.y * height;
    const radius = Math.max((acu.radius_px ?? 0.03) * width, 8);

    // 离线模式：颜色降级
    let fillColor: string;
    let strokeColor: string;
    let lineDash: number[] = [];

    if (isOffline) {
      fillColor = 'rgba(128, 128, 128, 0.2)';
      strokeColor = 'rgba(160, 160, 160, 0.5)';
    } else if (acu.confidence >= 0.7) {
      fillColor = 'rgba(255, 255, 0, 0.3)';
      strokeColor = 'rgba(255, 255, 0, 0.9)';
    } else if (acu.confidence >= 0.4) {
      fillColor = 'rgba(255, 255, 0, 0.15)';
      strokeColor = 'rgba(255, 255, 0, 0.5)';
    } else {
      fillColor = 'rgba(255, 255, 0, 0.05)';
      strokeColor = 'rgba(255, 0, 0, 0.5)';
      lineDash = [4, 4];
    }

    // 作用区域
    ctx.beginPath();
    ctx.arc(ax, ay, radius, 0, Math.PI * 2);
    ctx.fillStyle = fillColor;
    ctx.fill();

    ctx.setLineDash(lineDash);
    ctx.strokeStyle = strokeColor;
    ctx.lineWidth = 2;
    ctx.stroke();
    ctx.setLineDash([]);

    // 穴位中心点
    ctx.beginPath();
    ctx.arc(ax, ay, 4, 0, Math.PI * 2);
    ctx.fillStyle = isOffline ? 'rgba(180, 180, 180, 0.5)' : 'rgba(255, 255, 0, 1)';
    ctx.fill();

    // 专家修正点（离线时也变灰）
    if (acu.expert_corrected && acu.expert_corrected_x != null && acu.expert_corrected_y != null) {
      const cx = acu.expert_corrected_x * width;
      const cy = acu.expert_corrected_y * height;

      ctx.beginPath();
      ctx.moveTo(ax, ay);
      ctx.lineTo(cx, cy);
      ctx.strokeStyle = isOffline ? 'rgba(100, 100, 100, 0.4)' : 'rgba(0, 100, 255, 0.6)';
      ctx.lineWidth = 1;
      ctx.setLineDash([3, 3]);
      ctx.stroke();
      ctx.setLineDash([]);

      ctx.beginPath();
      ctx.arc(cx, cy, 6, 0, Math.PI * 2);
      ctx.fillStyle = isOffline ? 'rgba(150, 150, 150, 0.5)' : 'rgba(0, 100, 255, 0.8)';
      ctx.fill();
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.8)';
      ctx.lineWidth = 2;
      ctx.stroke();
    }

    // 穴位名称标签
    ctx.font = 'bold 13px sans-serif';
    const suffix = isOffline ? ' (缓存)' : '';
    const label = `${acu.name_cn}(${acu.id}) ${Math.round(acu.confidence * 100)}%${suffix}`;
    const textWidth = ctx.measureText(label).width;
    const labelX = ax - textWidth / 2;
    const labelY = ay - radius - 6;

    ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
    ctx.fillRect(labelX - 4, labelY - 13, textWidth + 8, 18);

    const labelColor = isOffline ? '#AAAAAA'
      : acu.confidence >= 0.7 ? '#FFD700'
      : acu.confidence >= 0.4 ? '#FFFFAA'
      : '#FF8888';
    ctx.fillStyle = labelColor;
    ctx.fillText(label, labelX, labelY);
  }
}

/** 步骤 5 — 绘制朝向标签 */
export function drawOrientationLabels(
  ctx: CanvasRenderingContext2D,
  bodyOrientation: any,
  handOrientations: any[],
  width: number,
  height: number,
) {
  // 身体朝向
  if (bodyOrientation) {
    const orientText = `人体: ${ORIENT_LABELS[bodyOrientation.orientation] || bodyOrientation.orientation} (${Math.round(bodyOrientation.confidence * 100)}%)`;
    ctx.font = 'bold 14px sans-serif';
    ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
    const tw = ctx.measureText(orientText).width;
    ctx.fillRect(8, 8, tw + 16, 24);
    ctx.fillStyle = '#00FF00';
    ctx.fillText(orientText, 16, 26);
  }

  // 手部朝向
  for (let i = 0; i < handOrientations.length; i++) {
    const ho = handOrientations[i];
    const hoText = `${ho.hand_id}: ${ho.orientation} (${Math.round(ho.confidence * 100)}%)`;
    ctx.font = '12px sans-serif';
    const tw = ctx.measureText(hoText).width;
    ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
    ctx.fillRect(8, 36 + i * 22, tw + 16, 20);
    ctx.fillStyle = '#FFA500';
    ctx.fillText(hoText, 16, 50 + i * 22);
  }
}

/** 步骤 6 — 绘制状态提示 + 离线降级遮罩 */
export function drawStatusOverlay(
  ctx: CanvasRenderingContext2D,
  result: WSResult,
  width: number,
  height: number,
  isOffline: boolean,
) {
  const acupoints = result.acupoint_result.acupoints;
  const visibleCount = acupoints.filter((a: any) => a.visible).length;
  const orientLabel = result.acupoint_result.body_orientation?.orientation || 'unknown';

  // 无检测提示
  if (!result.pose.has_body) {
    ctx.font = 'bold 18px sans-serif';
    ctx.fillStyle = 'rgba(255, 80, 80, 0.9)';
    ctx.textAlign = 'center';
    ctx.fillText('未检测到人体 — 请正对摄像头', width / 2, height / 2);

    if (result.pose.has_hands) {
      ctx.fillStyle = 'rgba(255, 200, 0, 0.9)';
      ctx.fillText('但检测到手部，手部穴位可能可见', width / 2, height / 2 + 28);
    }
    ctx.textAlign = 'start';
  } else if (visibleCount === 0 && orientLabel === 'partial_front') {
    ctx.font = 'bold 16px sans-serif';
    ctx.fillStyle = 'rgba(255, 200, 0, 0.9)';
    ctx.textAlign = 'center';
    ctx.fillText('面部已检测，正在计算穴位...', width / 2, height / 2);
    ctx.textAlign = 'start';
  }

  // 离线降级遮罩 (B15)
  if (isOffline) {
    ctx.fillStyle = 'rgba(0, 0, 0, 0.3)';
    ctx.fillRect(0, 0, width, height);

    ctx.font = 'bold 20px sans-serif';
    ctx.fillStyle = 'rgba(255, 180, 0, 0.9)';
    ctx.textAlign = 'center';
    ctx.fillText('离线模式 — 显示缓存结果', width / 2, 40);

    ctx.font = '14px sans-serif';
    ctx.fillStyle = 'rgba(255, 255, 255, 0.6)';
    ctx.fillText('正在尝试重新连接...', width / 2, height - 30);
    ctx.textAlign = 'start';
  }

  // 区域穴位计数标签 (在线时显示)
  if (visibleCount > 0 && !isOffline) {
    const faceVis = acupoints.filter((a: any) => a.visible && FACE_ACUPOINT_IDS.has(a.id));
    const handVis = acupoints.filter((a: any) => a.visible && HAND_ACUPOINT_IDS.has(a.id));
    const bodyVis = acupoints.filter((a: any) => a.visible && !FACE_ACUPOINT_IDS.has(a.id) && !HAND_ACUPOINT_IDS.has(a.id));

    const parts: string[] = [];
    if (faceVis.length > 0) parts.push(`面部:${faceVis.length}`);
    if (handVis.length > 0) parts.push(`手部:${handVis.length}`);
    if (bodyVis.length > 0) parts.push(`身体:${bodyVis.length}`);

    const statusText = parts.join(' ') + ` | 共${visibleCount}穴`;
    ctx.font = 'bold 14px sans-serif';
    const sw = ctx.measureText(statusText).width;
    ctx.fillStyle = 'rgba(0, 0, 0, 0.75)';
    ctx.fillRect(width - sw - 20, height - 34, sw + 16, 26);
    ctx.fillStyle = '#00FF88';
    ctx.fillText(statusText, width - sw - 12, height - 16);
  }
}
