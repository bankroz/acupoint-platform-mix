import { useEffect, useRef, useState, useCallback } from 'react';
import { wsDisconnect } from '../store/wsStore';

/**
 * 摄像头管理 Hook。
 *
 * R9: 监听 track ended 事件，检测权限中途撤销。
 * R17: 优雅的错误消息映射，替代裸 err.message。
 * 解耦-F3: 复用离屏 canvas，避免每帧创建新 canvas。
 */

const CAMERA_ERROR_MESSAGES: Record<string, string> = {
  NotAllowedError: '摄像头访问被拒绝，请在浏览器地址栏点击摄像头图标重新授权',
  NotFoundError: '未检测到摄像头设备，请确认已连接并被系统识别',
  NotReadableError: '摄像头被其他程序占用，请关闭其他视频应用后重试',
  OverconstrainedError: '摄像头不支持所需分辨率，请尝试其他摄像头',
  AbortError: '摄像头启动被中断，请重试',
};

export function useCamera() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [active, setActive] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const offscreenCanvasRef = useRef<HTMLCanvasElement | null>(null);

  const start = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 640 },
          height: { ideal: 480 },
          facingMode: 'user',
        },
      });
      streamRef.current = stream;

      // R9: 监听 track 权限撤销
      const videoTrack = stream.getVideoTracks()[0];
      if (videoTrack) {
        videoTrack.addEventListener('ended', () => {
          setError('摄像头访问权限已被撤销，请刷新页面重新授权');
          setActive(false);
          wsDisconnect();
        });
      }

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      setActive(true);
      setError(null);
    } catch (err: any) {
      // R17: 友好错误消息
      const friendlyMsg = CAMERA_ERROR_MESSAGES[err.name] ?? `摄像头错误：${err.message}`;
      setError(friendlyMsg);
      setActive(false);
    }
  };

  const stop = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setActive(false);
  };

  /** 从 video 元素抓取当前帧的 base64 JPEG — 复用离屏 canvas (解耦-F3) */
  const captureFrame = useCallback((): string | null => {
    if (!videoRef.current || !active) return null;
    const video = videoRef.current;
    if (video.readyState < 2) return null;

    if (!offscreenCanvasRef.current) {
      offscreenCanvasRef.current = document.createElement('canvas');
    }
    const canvas = offscreenCanvasRef.current;
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;

    const ctx = canvas.getContext('2d');
    if (!ctx) return null;
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    return canvas.toDataURL('image/jpeg', 0.7);
  }, [active]);

  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop());
      }
    };
  }, []);

  return { videoRef, active, error, start, stop, captureFrame };
}
