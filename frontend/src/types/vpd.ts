export interface VPDGridResponse {
  grid_id: string;
  temps: number[];
  rhs: number[];
  matrix: number[][];
}

export interface VPDSettingResponse {
  id: number;
  name: string;
  target_min_kpa: number;
  target_max_kpa: number;
  temp_constraint_min: number | null;
  temp_constraint_max: number | null;
  rh_constraint_min: number | null;
  rh_constraint_max: number | null;
  metric_key: string;
  recommend_mode: string;
  created_at: string;
}

export interface RecommendResponse {
  temp_c: number | null;
  rh_pct: number | null;
  vpd_kpa: number | null;
  margin: number | null;
  sensitivity: { dVPD_dT: number | null; dVPD_dRH: number | null };
  message: string;
}

export interface OverlayPoint {
  run_id: string;
  temp_c: number;
  rh_pct: number;
  vpd_kpa: number;
  metric_value: number;
  tool_id: string;
  recipe_id: string;
  batch_id: string;
  started_at: string | null;
}

export interface DOERunDetail {
  run_id: string;
  tool_id: string | null;
  recipe_id: string | null;
  batch_id: string | null;
  started_at: string | null;
  ended_at: string | null;
  factors: Record<string, number>;
  measurements: { metric_key: string; metric_value: number; unit?: string }[];
  notes: string | null;
}

export interface MainEffectsEffect {
  factor: string;
  levels: number[];
  means: number[];
  counts: number[];
}

export interface ImportanceItem {
  factor: string;
  importance: number;
}
