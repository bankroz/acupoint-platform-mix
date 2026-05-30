import React, { useEffect, useCallback } from 'react';
import { useCamera } from '../hooks/useCamera';
import { useWsStore, wsConnect, wsDisconnect, wsSendFrame } from '../store/wsStore';
import { OverlayCanvas } from './OverlayCanvas';

export const CameraView: React.FC = () => {
  const { videoRef, active, error, start, stop, captureFrame } = useCamera();
  const latestResult = useWsStore((s) => s.latestResult);
  const wsConnected = useWsStore((s) => s.wsConnected);
  const pendingFrame = useWsStore((s) => s.pendingFrame);
  const lastCachedResult = useWsStore((s) => s.lastCachedResult);

  const [videoSize, setVideoSize] = React.useState({ w: 640, h: 480 });

  const handleStart = useCallback(() => {
    start();
    wsConnect();
  }, [start]);

  const handleStop = useCallback(() => {
    stop();
    wsDisconnect();
  }, [stop]);

  // 帧发送循环 — 背压控制 (B2)
  useEffect(() => {
    if (!active || !wsConnected) return;

    const interval = setInterval(() => {
      // 背压：只有在无 pending 帧时才捕获和发送
      if (pendingFrame) return;

      const frame = captureFrame();
      if (frame) {
        wsSendFrame(frame);
      }
    }, 150); // 约 6-7 fps，与 FRAME_INTERVAL_MS 对齐

    return () => clearInterval(interval);
  }, [active, wsConnected, pendingFrame, captureFrame]);

  // 监听视频 intrinsic 尺寸（后端归一化坐标基准）
  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const setIntrinsicSize = () => {
      setVideoSize({
        w: video.videoWidth || 640,
        h: video.videoHeight || 480,
      });
    };

    setIntrinsicSize();
    video.addEventListener('loadedmetadata', setIntrinsicSize);
    return () => video.removeEventListener('loadedmetadata', setIntrinsicSize);
  }, [videoRef, active]);

  // 用于 OverlayCanvas 的数据：在线用实时结果，离线用缓存
  const displayResult = wsConnected ? latestResult : lastCachedResult;

  return (
    <div className="relative bg-black rounded-lg overflow-hidden">
      {/* 视频始终挂载，用 CSS visibility 控制，确保 start() 时 videoRef 始终可用 */}
      <video
        ref={videoRef}
        className="w-full block"
        style={{ visibility: active ? 'visible' : 'hidden', opacity: active ? 1 : 0 }}
        playsInline
        muted
      />

      {active && (
        <OverlayCanvas
          result={displayResult}
          width={videoSize.w || 640}
          height={videoSize.h || 480}
          isOffline={!wsConnected}
        />
      )}

      {!active && (
        <div className="flex flex-col items-center justify-center h-64 absolute inset-0 bg-gray-900/90">
          <p className="text-gray-400 mb-4">摄像头未启动</p>
          <button
            onClick={handleStart}
            className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition"
          >
            开启摄像头
          </button>
          {error && <p className="text-red-400 mt-2 text-sm">{error}</p>}
        </div>
      )}

      {active && (
        <div className="absolute top-2 right-2 z-20 flex gap-2">
          <span className={`px-2 py-0.5 rounded text-xs text-white ${
            wsConnected ? 'bg-green-600' : 'bg-red-600'
          }`}>
            {wsConnected ? 'WS 已连接' : 'WS 断开'}
          </span>
          {!wsConnected && (
            <span className="px-2 py-0.5 rounded text-xs bg-yellow-600 text-white">
              重连中...
            </span>
          )}
          <span className={`px-2 py-0.5 rounded text-xs ${
            pendingFrame ? 'bg-yellow-600' : 'bg-gray-600'
          } text-white`}>
            {pendingFrame ? '处理中' : '空闲'}
          </span>
          <button
            onClick={handleStop}
            className="px-3 py-0.5 bg-red-600 text-white rounded text-xs hover:bg-red-700"
          >
            关闭
          </button>
        </div>
      )}
    </div>
  );
};
