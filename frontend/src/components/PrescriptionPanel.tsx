import React from 'react';

const MOCK_PRESCRIPTION = {
  prescription_id: 'rx_demo',
  diagnosis: '肩颈紧张',
  target_regions: ['neck', 'shoulder', 'upper_back'],
  recommended_acupoints: ['GB20', 'GB21', 'GV14', 'LI4'],
  therapy_plan: [
    { step: 1, region: 'neck', acupoint_ids: ['GB20'], device: '温震终端', duration_sec: 180, intensity: '低', notes: '询问酸胀感' },
    { step: 2, region: 'shoulder', acupoint_ids: ['GB21'], device: '温震终端', duration_sec: 240, intensity: '中', notes: '双侧肩井' },
  ],
  contraindications: ['孕妇禁用肩井穴'],
  created_by: '系统Demo',
};

export const PrescriptionPanel: React.FC = () => {
  return (
    <div className="bg-gray-800 rounded-lg p-4">
      <h3 className="text-white font-bold text-lg mb-3">诊疗处方 (Demo)</h3>
      <div className="text-sm space-y-2">
        <div className="flex justify-between">
          <span className="text-gray-400">诊断:</span>
          <span className="text-white font-medium">{MOCK_PRESCRIPTION.diagnosis}</span>
        </div>
        <div>
          <span className="text-gray-400">目标区域:</span>
          <div className="flex gap-1 mt-1">
            {MOCK_PRESCRIPTION.target_regions.map((r) => (
              <span key={r} className="px-2 py-0.5 bg-purple-900 text-purple-300 rounded text-xs">{r}</span>
            ))}
          </div>
        </div>
        <div>
          <span className="text-gray-400">推荐穴位:</span>
          <div className="flex gap-1 mt-1">
            {MOCK_PRESCRIPTION.recommended_acupoints.map((a) => (
              <span key={a} className="px-2 py-0.5 bg-yellow-900 text-yellow-300 rounded text-xs">{a}</span>
            ))}
          </div>
        </div>

        <div className="border-t border-gray-700 pt-2 mt-2">
          <span className="text-gray-400 text-xs font-bold">理疗步骤:</span>
          {MOCK_PRESCRIPTION.therapy_plan.map((step) => (
            <div key={step.step} className="mt-2 p-2 bg-gray-700 rounded">
              <div className="flex justify-between text-xs">
                <span className="text-blue-400">步骤 {step.step}</span>
                <span className="text-gray-400">{step.region}</span>
              </div>
              <div className="text-xs text-gray-300 mt-1">
                <span>设备: {step.device}</span>
                <span className="ml-2">时长: {step.duration_sec}s</span>
                <span className="ml-2">强度: {step.intensity}</span>
              </div>
              <p className="text-gray-500 text-xs mt-1">{step.notes}</p>
            </div>
          ))}
        </div>

        {MOCK_PRESCRIPTION.contraindications.length > 0 && (
          <div className="p-2 bg-red-900/50 rounded">
            <p className="text-red-400 text-xs font-bold">禁忌:</p>
            {MOCK_PRESCRIPTION.contraindications.map((c, i) => (
              <p key={i} className="text-red-300 text-xs">{c}</p>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
