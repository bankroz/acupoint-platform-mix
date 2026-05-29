import React, { useEffect, useCallback } from 'react';
import { useCamera } from '../hooks/useCamera';
import { useWebSocket } from '../hooks/useWebSocket';
import { useAppStore } from '../store/appStore';
import { OverlayCanvas } from './OverlayCanvas';

export const CameraView: React.FC = () => {
  const { videoRef, active, error, start, stop, captureFrame } = useCamera();
  const { connect, disconnect, sendFrame } = useWebSocket();
  const latestResult = useAppStore((s) => s.latestResult);
  const wsConnected = useAppStore((s) => s.wsConnected);
  const setCameraActive = useAppStore((s) => s.setCameraActive);

  const [videoSize, setVideoSize] = React.useState({ w: 640, h: 480 });

  const handleStart = useCallback(() => {
    start();
    connect();
    setCameraActive(true);
  }, [start, connect, setCameraActive]);

  const handleStop = useCallback(() => {
    stop();
    disconnect();
    setCameraActive(false);
  }, [stop, disconnect, setCameraActive]);

  // 帧发送循环
  useEffect(() => {
    if (!active || !wsConnected) return;
    const interval = setInterval(() => {
      const frame = captureFrame();
      if (frame) {
        sendFrame(frame);
      }
    }, 150); // 约 6-7 fps
    return () => clearInterval(interval);
  }, [active, wsConnected, captureFrame, sendFrame]);

  // 监听视频尺寸变化
  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;
    const updateSize = () => {
      setVideoSize({
        w: video.videoWidth || 640,
        h: video.videoHeight || 480,
      });
    };
    video.addEventListener('loadedmetadata', updateSize);
    return () => video.removeEventListener('loadedmetadata', updateSize);
  }, [videoRef, active]);

  return (
    <div className="relative bg-black rounded-lg overflow-hidden" style={{ minHeight: 400 }}>
      <video
        ref={videoRef}
        className="w-full"
        style={{ display: active ? 'block' : 'none', maxHeight: '60vh' }}
        playsInline
        muted
      />

      {!active && (
        <div className="flex flex-col items-center justify-center h-64 bg-gray-900">
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
          <span className={`px-2 py-0.5 rounded text-xs text-white ${wsConnected ? 'bg-green-600' : 'bg-red-600'}`}>
            {wsConnected ? 'WS 已连接' : 'WS 断开'}
          </span>
          <button
            onClick={handleStop}
            className="px-3 py-0.5 bg-red-600 text-white rounded text-xs hover:bg-red-700"
          >
            关闭
          </button>
        </div>
      )}

      <OverlayCanvas
        result={latestResult}
        width={videoSize.w || 640}
        height={videoSize.h || 480}
      />
    </div>
  );
};
