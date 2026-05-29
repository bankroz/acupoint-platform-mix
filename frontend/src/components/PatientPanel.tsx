import React from 'react';
import { useAppStore } from '../store/appStore';
import { useWebSocket } from '../hooks/useWebSocket';
import type { PatientProfile } from '../types';

export const PatientPanel: React.FC = () => {
  const patient = useAppStore((s) => s.patient);
  const setPatient = useAppStore((s) => s.setPatient);
  const { sendPatientUpdate } = useWebSocket();

  const handleChange = (field: keyof PatientProfile, value: string | number) => {
    const updated = { ...patient, [field]: value };
    // 自动计算 BMI
    if (field === 'height_cm' || field === 'weight_kg') {
      const h = (field === 'height_cm' ? value : patient.height_cm) as number;
      const w = (field === 'weight_kg' ? value : patient.weight_kg) as number;
      const heightM = h / 100;
      if (heightM > 0) {
        updated.bmi = Math.round((w / (heightM * heightM)) * 10) / 10;
        if (updated.bmi < 18.5) updated.body_type = 'thin';
        else if (updated.bmi < 25) updated.body_type = 'normal';
        else if (updated.bmi < 30) updated.body_type = 'overweight';
        else updated.body_type = 'obese';
      }
    }
    setPatient(updated);
    sendPatientUpdate(updated);
  };

  return (
    <div className="bg-gray-800 rounded-lg p-4">
      <h3 className="text-white font-bold text-lg mb-3">患者参数</h3>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="text-gray-400 text-xs">患者ID</label>
          <input
            type="text"
            value={patient.patient_id}
            onChange={(e) => handleChange('patient_id', e.target.value)}
            className="w-full bg-gray-700 text-white rounded px-2 py-1 text-sm mt-1"
          />
        </div>
        <div>
          <label className="text-gray-400 text-xs">性别</label>
          <select
            value={patient.sex}
            onChange={(e) => handleChange('sex', e.target.value)}
            className="w-full bg-gray-700 text-white rounded px-2 py-1 text-sm mt-1"
          >
            <option value="male">男</option>
            <option value="female">女</option>
            <option value="other">其他</option>
          </select>
        </div>
        <div>
          <label className="text-gray-400 text-xs">身高 (cm)</label>
          <input
            type="number"
            value={patient.height_cm}
            onChange={(e) => handleChange('height_cm', parseFloat(e.target.value) || 170)}
            className="w-full bg-gray-700 text-white rounded px-2 py-1 text-sm mt-1"
            min="50" max="250"
          />
        </div>
        <div>
          <label className="text-gray-400 text-xs">体重 (kg)</label>
          <input
            type="number"
            value={patient.weight_kg}
            onChange={(e) => handleChange('weight_kg', parseFloat(e.target.value) || 65)}
            className="w-full bg-gray-700 text-white rounded px-2 py-1 text-sm mt-1"
            min="20" max="200"
          />
        </div>
        <div>
          <label className="text-gray-400 text-xs">年龄</label>
          <input
            type="number"
            value={patient.age}
            onChange={(e) => handleChange('age', parseInt(e.target.value) || 35)}
            className="w-full bg-gray-700 text-white rounded px-2 py-1 text-sm mt-1"
            min="0" max="150"
          />
        </div>
        <div>
          <label className="text-gray-400 text-xs">BMI</label>
          <div className="w-full bg-gray-700 text-white rounded px-2 py-1 text-sm mt-1">
            {patient.bmi ?? '-'} ({patient.body_type})
          </div>
        </div>
      </div>
    </div>
  );
};
