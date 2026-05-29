import { useEffect, useRef } from 'react';
import { useAppStore } from '../store/appStore';

const WS_URL = `ws://localhost:8765/ws/realtime`;

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const intervalRef = useRef<number | null>(null);
  const setLatestResult = useAppStore((s) => s.setLatestResult);
  const setWsConnected = useAppStore((s) => s.setWsConnected);

  const connect = () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('[WS] 已连接');
      setWsConnected(true);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'result') {
          setLatestResult(data);
        }
      } catch (e) {
        console.error('[WS] 消息解析失败:', e);
      }
    };

    ws.onerror = (e) => {
      console.error('[WS] 错误:', e);
    };

    ws.onclose = () => {
      console.log('[WS] 断开');
      setWsConnected(false);
      // 自动重连
      setTimeout(() => {
        if (wsRef.current?.readyState !== WebSocket.OPEN) {
          connect();
        }
      }, 3000);
    };
  };

  const sendFrame = (imageBase64: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'frame',
        image: imageBase64,
      }));
    }
  };

  const sendPatientUpdate = (patient: Record<string, unknown>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'patient_update',
        data: patient,
      }));
    }
  };

  const sendExpertCorrection = (correction: Record<string, unknown>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'expert_correction',
        data: correction,
      }));
    }
  };

  const disconnect = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setWsConnected(false);
  };

  useEffect(() => {
    return () => disconnect();
  }, []);

  return { connect, disconnect, sendFrame, sendPatientUpdate, sendExpertCorrection };
}
