/**
 * WebSocket Zustand Store — 统一管理 WebSocket 连接、消息收发、背压控制。
 *
 * 替代原有的 useWebSocket hook，所有组件共享同一 ws 实例和状态。
 * WebSocket 实例作为模块级变量，不存入 Zustand（Zustand 只存可序列化状态）。
 *
 * B2 帧背压控制：pendingFrame 锁 + 帧超时保护 + 帧间间隔下限。
 * B15 离线降级：断开时保留 lastCachedResult 供离线显示。
 */

import { create } from 'zustand';
import type { WSResult } from '../types';

const WS_URL = `ws://localhost:8765/ws/realtime`;
const FRAME_INTERVAL_MS = 150;  // 帧间最低间隔
const FRAME_TIMEOUT_MS = 1000;  // 单帧超时
const RECONNECT_DELAY_MS = 3000;

// ============================================================
// Zustand State — 仅可序列化、响应式状态
// ============================================================

interface WsState {
  wsConnected: boolean;
  latestResult: WSResult | null;
  pendingFrame: boolean;
  lastFrameTime: number;
  lastCachedResult: WSResult | null;

  // 内部 actions
  _setWsConnected: (connected: boolean) => void;
  _setLatestResult: (result: WSResult) => void;
  _releaseFrameLock: () => void;
  _setLastFrameTime: (time: number) => void;
}

export const useWsStore = create<WsState>((set) => ({
  wsConnected: false,
  latestResult: null,
  pendingFrame: false,
  lastFrameTime: 0,
  lastCachedResult: null,

  _setWsConnected: (connected) => set({ wsConnected: connected }),
  _setLatestResult: (result) => {
    set({
      latestResult: result,
      lastCachedResult: result,
      pendingFrame: false, // 收到回执，释放背压锁
    });
  },
  _releaseFrameLock: () => set({ pendingFrame: false }),
  _setLastFrameTime: (time) => set({ lastFrameTime: time }),
}));

// ============================================================
// WebSocket 实例 — 模块级单例
// ============================================================

let _ws: WebSocket | null = null;
let _reconnectTimer: ReturnType<typeof setTimeout> | null = null;
let _frameTimeoutTimer: ReturnType<typeof setTimeout> | null = null;

function _clearFrameTimeout() {
  if (_frameTimeoutTimer) {
    clearTimeout(_frameTimeoutTimer);
    _frameTimeoutTimer = null;
  }
}

// ============================================================
// 公开 API
// ============================================================

export function wsConnect() {
  if (_ws?.readyState === WebSocket.OPEN) return;

  const ws = new WebSocket(WS_URL);
  _ws = ws;

  ws.onopen = () => {
    console.log('[WS] 已连接');
    useWsStore.getState()._setWsConnected(true);
  };

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      switch (data.type) {
        case 'result':
          _clearFrameTimeout();
          useWsStore.getState()._setLatestResult(data);
          break;
        case 'skip':
          console.debug('[WS] 帧被跳过（服务端繁忙）');
          _clearFrameTimeout();
          useWsStore.getState()._releaseFrameLock();
          break;
        case 'timeout':
          console.warn('[WS] 帧处理超时');
          _clearFrameTimeout();
          useWsStore.getState()._releaseFrameLock();
          break;
        case 'ack':
          console.log('[WS] 服务器确认:', data.message);
          break;
        case 'pong':
          break;
        case 'error':
          console.error('[WS] 服务器错误:', data.message);
          break;
        default:
          console.debug('[WS] 未知消息类型:', data.type);
      }
    } catch (e) {
      console.error('[WS] 消息解析失败:', e);
    }
  };

  ws.onerror = (e) => {
    console.error('[WS] 连接错误:', e);
  };

  ws.onclose = () => {
    console.log(`[WS] 断开，${RECONNECT_DELAY_MS / 1000}s 后自动重连...`);
    useWsStore.getState()._setWsConnected(false);
    useWsStore.getState()._releaseFrameLock();
    _ws = null;
    _clearFrameTimeout();

    // 自动重连
    _reconnectTimer = setTimeout(() => {
      if (_ws?.readyState !== WebSocket.OPEN) {
        wsConnect();
      }
    }, RECONNECT_DELAY_MS);
  };
}

export function wsDisconnect() {
  if (_reconnectTimer) {
    clearTimeout(_reconnectTimer);
    _reconnectTimer = null;
  }
  _clearFrameTimeout();
  if (_ws) {
    _ws.close();
    _ws = null;
  }
  useWsStore.getState()._setWsConnected(false);
  useWsStore.getState()._releaseFrameLock();
}

/**
 * 发送视频帧 — 带背压控制 (B2)
 *
 * @returns true 表示已发送，false 表示被拦截（上一帧未回执 / 帧间间隔不足）
 */
export function wsSendFrame(imageBase64: string): boolean {
  const state = useWsStore.getState();

  // 背压检查 1：上一帧未回执
  if (state.pendingFrame) {
    return false;
  }

  // 背压检查 2：帧间最低间隔 150ms
  const now = Date.now();
  if (state.lastFrameTime > 0 && (now - state.lastFrameTime) < FRAME_INTERVAL_MS) {
    return false;
  }

  if (_ws?.readyState === WebSocket.OPEN) {
    _ws.send(JSON.stringify({ type: 'frame', image: imageBase64 }));
    useWsStore.setState({ pendingFrame: true, lastFrameTime: now });

    // 超时保护：超过 FRAME_TIMEOUT_MS 未收到回执则释放锁
    _frameTimeoutTimer = setTimeout(() => {
      if (useWsStore.getState().pendingFrame) {
        console.warn('[WS] 帧超时（无回执），释放背压锁');
        useWsStore.getState()._releaseFrameLock();
      }
    }, FRAME_TIMEOUT_MS);

    return true;
  }
  return false;
}

export function wsSendPatientUpdate(patient: Record<string, unknown>) {
  if (_ws?.readyState === WebSocket.OPEN) {
    _ws.send(JSON.stringify({ type: 'patient_update', data: patient }));
  }
}

export function wsSendExpertCorrection(correction: Record<string, unknown>) {
  if (_ws?.readyState === WebSocket.OPEN) {
    _ws.send(JSON.stringify({ type: 'expert_correction', data: correction }));
  }
}
