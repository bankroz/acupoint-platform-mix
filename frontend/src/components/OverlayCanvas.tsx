/**
 * Canvas 叠加层组件。
 *
 * 在视频画面上方透明 canvas 绘制骨架、手部、经络、穴位标注。
 * 支持在线/离线两种模式 (B15 离线降级)。
 *
 * 渲染逻辑已拆分为 canvas-renderers.ts（解耦-F1）。
 */

import React, { useRef, useEffect } from 'react';
import type { WSResult } from '../types';
import {
  drawSkeleton,
  drawHandKeypoints,
  drawMeridians,
  drawAcupoints,
  drawOrientationLabels,
  drawStatusOverlay,
} from '../utils/canvas-renderers';

interface Props {
  result: WSResult | null;
  width: number;
  height: number;
  isOffline?: boolean;
}

export const OverlayCanvas: React.FC<Props> = ({ result, width, height, isOffline = false }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.clearRect(0, 0, width, height);

    if (!result) return;

    // 1. 骨架线 + 关键点
    drawSkeleton(ctx, result.pose.body_keypoints, width, height);

    // 2. 手部关键点
    drawHandKeypoints(ctx, result.pose.hands, width, height);

    // 3. 经络线
    drawMeridians(ctx, result.pose.body_keypoints, width, height);

    // 4. 穴位标注
    drawAcupoints(ctx, result.acupoint_result.acupoints, width, height, isOffline);

    // 5. 朝向标签
    drawOrientationLabels(
      ctx,
      result.acupoint_result.body_orientation,
      result.acupoint_result.hand_orientations,
      width,
      height,
    );

    // 6. 状态提示 + 离线遮罩
    drawStatusOverlay(ctx, result, width, height, isOffline);

  }, [result, width, height, isOffline]);

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
