import React, { useRef, useEffect } from 'react';
import type { WSResult, BodyKeypoint, AcupointEstimate } from '../types';

// 骨架连接 (YOLOv8-Pose COCO 17 keypoints)
const SKELETON_PAIRS: [string, string][] = [
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

// 经络连接（简化版）
const MERIDIAN_PAIRS: [string, string][] = [
  // 手太阴肺经简化
  ['left_shoulder', 'left_elbow'],
  ['left_elbow', 'left_wrist'],
  ['right_shoulder', 'right_elbow'],
  ['right_elbow', 'right_wrist'],
];

interface Props {
  result: WSResult | null;
  width: number;
  height: number;
}

export const OverlayCanvas: React.FC<Props> = ({ result, width, height }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // 半透明清除（保留视频画面）
    ctx.clearRect(0, 0, width, height);

    if (!result) return;

    const kps = result.pose.body_keypoints;

    // === 1. 绘制骨架线 ===
    ctx.strokeStyle = 'rgba(0, 255, 0, 0.6)';
    ctx.lineWidth = 2;
    const kpMap = new Map<string, BodyKeypoint>();
    kps.forEach((kp) => kpMap.set(kp.name, kp));

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

    // === 2. 绘制骨架关键点 ===
    kps.forEach((kp) => {
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

    // === 3. 绘制手部关键点 ===
    for (const hand of result.pose.hands) {
      if (!hand.landmarks || hand.landmarks.length < 21) continue;

      // 手部骨架线
      const handConnections = [
        [0, 1], [1, 2], [2, 3], [3, 4],   // 拇指
        [0, 5], [5, 6], [6, 7], [7, 8],   // 食指
        [0, 9], [9, 10], [10, 11], [11, 12], // 中指
        [0, 13], [13, 14], [14, 15], [15, 16], // 无名指
        [0, 17], [17, 18], [18, 19], [19, 20], // 小指
        [5, 9], [9, 13], [13, 17],  // 横向连接
      ];

      ctx.strokeStyle = 'rgba(255, 165, 0, 0.5)';
      ctx.lineWidth = 1.5;
      for (const [ai, bi] of handConnections) {
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
      hand.landmarks.slice(0, 21).forEach((lm) => {
        ctx.beginPath();
        ctx.arc(lm.x * width, lm.y * height, 3, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(255, 165, 0, 0.8)';
        ctx.fill();
      });
    }

    // === 4. 绘制经络线 ===
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

    // === 5. 绘制穴位 ===
    const acupoints = result.acupoint_result.acupoints;

    for (const acu of acupoints) {
      if (!acu.visible || acu.x == null || acu.y == null) continue;

      const ax = acu.x * width;
      const ay = acu.y * height;
      const radius = Math.max(acu.radius_px * width, 8);

      // 置信度决定颜色和样式
      let fillColor: string;
      let strokeColor: string;
      let lineDash: number[] = [];

      if (acu.confidence >= 0.7) {
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
      ctx.fillStyle = 'rgba(255, 255, 0, 1)';
      ctx.fill();

      // 专家修正点（蓝色）
      if (acu.expert_corrected && acu.expert_corrected_x != null && acu.expert_corrected_y != null) {
        const cx = acu.expert_corrected_x * width;
        const cy = acu.expert_corrected_y * height;

        // AI 原点 → 修正点连线
        ctx.beginPath();
        ctx.moveTo(ax, ay);
        ctx.lineTo(cx, cy);
        ctx.strokeStyle = 'rgba(0, 100, 255, 0.6)';
        ctx.lineWidth = 1;
        ctx.setLineDash([3, 3]);
        ctx.stroke();
        ctx.setLineDash([]);

        // 修正点
        ctx.beginPath();
        ctx.arc(cx, cy, 6, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(0, 100, 255, 0.8)';
        ctx.fill();
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.8)';
        ctx.lineWidth = 2;
        ctx.stroke();
      }

      // 穴位名称标签
      ctx.font = 'bold 13px sans-serif';
      const label = `${acu.name_cn}(${acu.id}) ${Math.round(acu.confidence * 100)}%`;
      const textWidth = ctx.measureText(label).width;
      const labelX = ax - textWidth / 2;
      const labelY = ay - radius - 6;

      // 标签背景
      ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
      ctx.fillRect(labelX - 4, labelY - 13, textWidth + 8, 18);

      // 标签文字
      ctx.fillStyle = acu.confidence >= 0.7 ? '#FFD700' : acu.confidence >= 0.4 ? '#FFFFAA' : '#FF8888';
      ctx.fillText(label, labelX, labelY);
    }

    // === 6. 朝向标签 ===
    const orient = result.acupoint_result.body_orientation;
    const ORIENT_LABELS: Record<string, string> = {
      front: '正面', back: '背面', left_side: '左侧', right_side: '右侧',
      partial_front: '部分正面', unknown: '未知',
    };
    if (orient) {
      const orientText = `人体: ${ORIENT_LABELS[orient.orientation] || orient.orientation} (${Math.round(orient.confidence * 100)}%)`;
      ctx.font = 'bold 14px sans-serif';
      ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
      const tw = ctx.measureText(orientText).width;
      ctx.fillRect(8, 8, tw + 16, 24);
      ctx.fillStyle = '#00FF00';
      ctx.fillText(orientText, 16, 26);
    }

    // 手部朝向
    const handOrs = result.acupoint_result.hand_orientations;
    for (let i = 0; i < handOrs.length; i++) {
      const ho = handOrs[i];
      const hoText = `${ho.hand_id}: ${ho.orientation} (${Math.round(ho.confidence * 100)}%)`;
      ctx.font = '12px sans-serif';
      const tw = ctx.measureText(hoText).width;
      ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
      ctx.fillRect(8, 36 + i * 22, tw + 16, 20);
      ctx.fillStyle = '#FFA500';
      ctx.fillText(hoText, 16, 50 + i * 22);
    }

    // === 7. 状态提示 ===
    const visibleCount = acupoints.filter(a => a.visible).length;
    const orientLabel = orient?.orientation || 'unknown';

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
      // 面部已检测但穴位不可见
      ctx.font = 'bold 16px sans-serif';
      ctx.fillStyle = 'rgba(255, 200, 0, 0.9)';
      ctx.textAlign = 'center';
      ctx.fillText('面部已检测，正在计算穴位...', width / 2, height / 2);
      ctx.textAlign = 'start';
    }

    // 区域穴位计数标签
    if (visibleCount > 0) {
      const faceVisibleAcus = acupoints.filter(a => a.visible && a.id && ['EX-HN3','EX-HN5','LI20','ST2'].includes(a.id));
      const handVisibleAcus = acupoints.filter(a => a.visible && a.id && ['LI4','PC8','PC6'].includes(a.id));
      const bodyVisibleAcus = acupoints.filter(a => a.visible && a.id && !['EX-HN3','EX-HN5','LI20','ST2','LI4','PC8','PC6'].includes(a.id));

      const parts = [];
      if (faceVisibleAcus.length > 0) parts.push(`面部:${faceVisibleAcus.length}`);
      if (handVisibleAcus.length > 0) parts.push(`手部:${handVisibleAcus.length}`);
      if (bodyVisibleAcus.length > 0) parts.push(`身体:${bodyVisibleAcus.length}`);

      const statusText = parts.join(' ') + ` | 共${visibleCount}穴`;
      ctx.font = 'bold 14px sans-serif';
      const sw = ctx.measureText(statusText).width;
      ctx.fillStyle = 'rgba(0, 0, 0, 0.75)';
      ctx.fillRect(width - sw - 20, height - 34, sw + 16, 26);
      ctx.fillStyle = '#00FF88';
      ctx.fillText(statusText, width - sw - 12, height - 16);
    }

  }, [result, width, height]);

  return (
    <canvas
      ref={canvasRef}
      width={width}
      height={height}
      className="absolute top-0 left-0 pointer-events-none"
      style={{ zIndex: 10 }}
    />
  );
};
