import { create } from 'zustand';
import type { WSResult, PatientProfile } from '../types';

interface AppState {
  // 实时数据
  latestResult: WSResult | null;
  // 连接状态
  wsConnected: boolean;
  // 摄像头状态
  cameraActive: boolean;
  // 患者信息
  patient: PatientProfile;
  // 状态颜色
  setLatestResult: (result: WSResult) => void;
  setWsConnected: (connected: boolean) => void;
  setCameraActive: (active: boolean) => void;
  setPatient: (patient: PatientProfile) => void;
}

export const useAppStore = create<AppState>((set) => ({
  latestResult: null,
  wsConnected: false,
  cameraActive: false,
  patient: {
    patient_id: 'p_demo',
    height_cm: 170,
    weight_kg: 65,
    age: 35,
    sex: 'male',
    bmi: 22.5,
    body_type: 'normal',
    notes: '',
  },

  setLatestResult: (result) => set({ latestResult: result }),
  setWsConnected: (connected) => set({ wsConnected: connected }),
  setCameraActive: (active) => set({ cameraActive: active }),
  setPatient: (patient) => set({ patient }),
}));
