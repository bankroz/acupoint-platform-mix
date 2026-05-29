// === 基础类型定义 ===

export interface BodyKeypoint {
  name: string;
  x: number;
  y: number;
  confidence: number;
}

export interface HandLandmark {
  name: string;
  x: number;
  y: number;
  confidence: number;
}

export interface HandData {
  hand_id: string;
  confidence: number;
  landmarks: HandLandmark[];
}

export interface BodyOrientation {
  orientation: 'front' | 'back' | 'left_side' | 'right_side' | 'partial_front' | 'unknown';
  confidence: number;
  reasons: string[];
}

export interface HandOrientation {
  hand_id: string;
  orientation: 'palm' | 'back_of_hand' | 'side' | 'unknown';
  confidence: number;
  reasons: string[];
}

export interface AcupointEstimate {
  id: string;
  name_cn: string;
  name_en: string;
  meridian: string;
  x: number | null;
  y: number | null;
  z: number | null;
  radius_px: number;
  confidence: number;
  source: string;
  orientation_valid: boolean;
  requires_expert_confirm: boolean;
  warnings: string[];
  visible: boolean;
  expert_corrected_x: number | null;
  expert_corrected_y: number | null;
  expert_corrected: boolean;
}

export interface WSResult {
  type: string;
  timestamp: number;
  pose: {
    has_body: boolean;
    has_hands: boolean;
    body_keypoints: BodyKeypoint[];
    hands: HandData[];
  };
  acupoint_result: {
    frame_id: string;
    body_orientation: BodyOrientation | null;
    hand_orientations: HandOrientation[];
    cun_result: {
      estimates: Array<{ method: string; cun_px: number; confidence: number }>;
      selected: { method: string; cun_px: number; confidence: number } | null;
    } | null;
    acupoints: AcupointEstimate[];
    correction_factors: Record<string, unknown>;
    warnings: string[];
  };
}

export interface PatientProfile {
  patient_id: string;
  height_cm: number;
  weight_kg: number;
  age: number;
  sex: 'male' | 'female' | 'other';
  bmi: number | null;
  body_type: string;
  notes: string;
}
