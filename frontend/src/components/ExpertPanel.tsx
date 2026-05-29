import React, { useState, useCallback } from 'react';
import { useAppStore } from '../store/appStore';
import { useWsStore, wsSendExpertCorrection } from '../store/wsStore';
import type { AcupointEstimate } from '../types';

const CORRECTION_REASONS = [
  '体型差异', '姿态差异', '关键点识别错误', '同身寸估算错误',
  '左右侧判断错误', '正反面判断错误', '手掌手背判断错误',
  '专家经验判断', '穴位定义文件错误', '图像遮挡', '其他',
];

/** 生成简单 UUID v4 (R4: 客户端唯一修正 ID) */
function generateUUID(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

export const ExpertPanel: React.FC = () => {
  const result = useAppStore((s) => s.latestResult);
  const patient = useAppStore((s) => s.patient);
  const wsConnected = useWsStore((s) => s.wsConnected);

  const [selectedAcu, setSelectedAcu] = useState<string | null>(null);
  const [dragX, setDragX] = useState<number>(0);
  const [dragY, setDragY] = useState<number>(0);
  const [reason, setReason] = useState('');
  const [notes, setNotes] = useState('');
  const [statusMsg, setStatusMsg] = useState('');
  const [submitting, setSubmitting] = useState(false);  // R4: 防重复提交

  const acupoints = result?.acupoint_result?.acupoints || [];
  const current = acupoints.find((a) => a.id === selectedAcu);

  const handleSelectAcu = (acu: AcupointEstimate) => {
    setSelectedAcu(acu.id);
    setDragX(acu.expert_corrected_x ?? acu.x ?? 0);
    setDragY(acu.expert_corrected_y ?? acu.y ?? 0);
    setReason('');
    setNotes('');
    setStatusMsg('');
  };

  const handleSubmitCorrection = useCallback(async () => {
    if (!selectedAcu || !current || submitting) return;

    const correctionId = generateUUID();  // R4: 客户端唯一 ID

    const correction = {
      correction_id: correctionId,
      patient_id: patient.patient_id,
      frame_id: result?.acupoint_result?.frame_id || '',
      acupoint_id: selectedAcu,
      ai_position: { x: current.x, y: current.y, z: null },
      corrected_position: { x: dragX, y: dragY, z: null },
      correction_distance_px: current.x
        ? Math.sqrt((dragX - current.x) ** 2 + (dragY - (current.y || 0)) ** 2) * 640
        : 0,
      correction_reasons: reason ? [reason] : [],
      expert_confidence: 0.9,
      notes: notes,
      algorithm_version: '0.1.0',
      acupoint_definition_version: '0.1.0',
    };

    setSubmitting(true);
    setStatusMsg('提交中...');

    try {
      if (wsConnected) {
        // 主通道：WebSocket
        wsSendExpertCorrection(correction);
      } else {
        // R2: 降级通道：REST API
        const resp = await fetch('/api/expert/correction', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(correction),
        });
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      }
      setStatusMsg(`穴位 ${selectedAcu} 已提交修正`);
    } catch (err: any) {
      setStatusMsg(`提交失败: ${err.message}`);
    } finally {
      setSubmitting(false);
      setTimeout(() => setStatusMsg(''), 3000);
    }
  }, [selectedAcu, current, submitting, patient.patient_id, result, dragX, dragY, reason, notes, wsConnected]);

  return (
    <div className="bg-gray-800 rounded-lg p-4">
      <h3 className="text-white font-bold text-lg mb-3">专家修正</h3>

      {acupoints.length === 0 && (
        <p className="text-gray-500 text-sm">等待穴位数据...</p>
      )}

      {/* 穴位列表 */}
      <div className="space-y-1 mb-3 max-h-40 overflow-y-auto">
        {acupoints.map((acu) => (
          <button
            key={acu.id}
            onClick={() => handleSelectAcu(acu)}
            className={`w-full text-left px-2 py-1 rounded text-sm flex justify-between items-center ${
              selectedAcu === acu.id ? 'bg-blue-700 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            <span>{acu.name_cn} ({acu.id})</span>
            <span className={`text-xs ${acu.confidence >= 0.7 ? 'text-green-400' : acu.confidence >= 0.4 ? 'text-yellow-400' : 'text-red-400'}`}>
              {Math.round(acu.confidence * 100)}%
            </span>
          </button>
        ))}
      </div>

      {/* 修正表单 */}
      {current && (
        <div className="space-y-2">
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="text-gray-400 text-xs">AI 位置 X</label>
              <div className="bg-gray-700 text-yellow-400 px-2 py-1 rounded text-sm">
                {current.x?.toFixed(3) || '-'}
              </div>
            </div>
            <div>
              <label className="text-gray-400 text-xs">AI 位置 Y</label>
              <div className="bg-gray-700 text-yellow-400 px-2 py-1 rounded text-sm">
                {current.y?.toFixed(3) || '-'}
              </div>
            </div>
            <div>
              <label className="text-gray-400 text-xs">修正 X</label>
              <input
                type="number"
                value={dragX}
                onChange={(e) => setDragX(parseFloat(e.target.value) || 0)}
                step="0.001"
                className="w-full bg-blue-900 text-blue-300 rounded px-2 py-1 text-sm"
              />
            </div>
            <div>
              <label className="text-gray-400 text-xs">修正 Y</label>
              <input
                type="number"
                value={dragY}
                onChange={(e) => setDragY(parseFloat(e.target.value) || 0)}
                step="0.001"
                className="w-full bg-blue-900 text-blue-300 rounded px-2 py-1 text-sm"
              />
            </div>
          </div>

          <div>
            <label className="text-gray-400 text-xs">修正原因</label>
            <select
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className="w-full bg-gray-700 text-white rounded px-2 py-1 text-sm mt-1"
            >
              <option value="">-- 选择原因 --</option>
              {CORRECTION_REASONS.map((r) => (
                <option key={r} value={r}>{r}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-gray-400 text-xs">备注</label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="w-full bg-gray-700 text-white rounded px-2 py-1 text-sm mt-1 h-16 resize-none"
              placeholder="补充说明..."
            />
          </div>

          <button
            onClick={handleSubmitCorrection}
            disabled={submitting}
            className={`w-full py-2 rounded transition text-sm ${
              submitting
                ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                : 'bg-blue-600 text-white hover:bg-blue-700'
            }`}
          >
            {submitting ? '提交中...' : '提交修正'}
          </button>

          {statusMsg && (
            <p className="text-green-400 text-xs text-center">{statusMsg}</p>
          )}

          {/* 穴位警告 */}
          {current.warnings.length > 0 && (
            <div className="mt-2 p-2 bg-yellow-900/50 rounded">
              <p className="text-yellow-400 text-xs font-bold">警告:</p>
              {current.warnings.map((w, i) => (
                <p key={i} className="text-yellow-300 text-xs">{w}</p>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
