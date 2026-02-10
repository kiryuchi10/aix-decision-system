import { apiGet, apiPost, apiPut } from '@/app/apiClient';
import type {
  VPDGridResponse,
  VPDSettingResponse,
  RecommendResponse,
  OverlayPoint,
  DOERunDetail,
  MainEffectsEffect,
  ImportanceItem,
} from '../types/vpd';

const P = (path: string) => path;

export async function createVPDGrid(params: {
  temp_min: number;
  temp_max: number;
  temp_step: number;
  rh_min: number;
  rh_max: number;
  rh_step: number;
}): Promise<{ grid_id: string }> {
  return apiPost<typeof params, { grid_id: string }>(P('/vpd/grids'), params);
}

export async function getVPDGrid(gridId: string): Promise<VPDGridResponse> {
  return apiGet<VPDGridResponse>(P(`/vpd/grids/${encodeURIComponent(gridId)}`));
}

export async function listVPDSettings(): Promise<VPDSettingResponse[]> {
  return apiGet<VPDSettingResponse[]>(P('/vpd/settings'));
}

export async function createVPDSetting(body: {
  name: string;
  target_min_kpa: number;
  target_max_kpa: number;
  temp_constraint_min?: number;
  temp_constraint_max?: number;
  rh_constraint_min?: number;
  rh_constraint_max?: number;
  metric_key?: string;
  recommend_mode?: string;
}): Promise<VPDSettingResponse> {
  return apiPost<typeof body, VPDSettingResponse>(P('/vpd/settings'), body);
}

export async function updateVPDSetting(
  id: number,
  body: {
    name: string;
    target_min_kpa: number;
    target_max_kpa: number;
    temp_constraint_min?: number;
    temp_constraint_max?: number;
    rh_constraint_min?: number;
    rh_constraint_max?: number;
    metric_key?: string;
    recommend_mode?: string;
  }
): Promise<VPDSettingResponse> {
  return apiPut<typeof body, VPDSettingResponse>(P(`/vpd/settings/${id}`), body);
}

export async function getRecommend(settingId: number, gridId: string): Promise<RecommendResponse> {
  return apiPost<{ setting_id: number; grid_id: string }, RecommendResponse>(P('/vpd/recommend'), {
    setting_id: settingId,
    grid_id: gridId,
  });
}

export async function getOverlayPoints(params: {
  metric_key: string;
  date_from?: string;
  date_to?: string;
  tool_id?: string;
  recipe_id?: string;
  batch_id?: string;
}): Promise<{ metric_key: string; points: OverlayPoint[] }> {
  const q = new URLSearchParams();
  q.set('metric_key', params.metric_key);
  if (params.date_from) q.set('date_from', params.date_from);
  if (params.date_to) q.set('date_to', params.date_to);
  if (params.tool_id) q.set('tool_id', params.tool_id);
  if (params.recipe_id) q.set('recipe_id', params.recipe_id);
  if (params.batch_id) q.set('batch_id', params.batch_id);
  return apiGet<{ metric_key: string; points: OverlayPoint[] }>(P(`/doe/overlay-points?${q.toString()}`));
}

export async function getDOERunDetail(runId: string): Promise<DOERunDetail> {
  return apiGet<DOERunDetail>(P(`/doe/runs/${encodeURIComponent(runId)}`));
}

export async function getMainEffects(metricKey: string, factorKeys?: string, nBins?: number): Promise<{ metric_key: string; effects: MainEffectsEffect[] }> {
  const q = new URLSearchParams();
  q.set('metric_key', metricKey);
  if (factorKeys) q.set('factor_keys', factorKeys);
  if (nBins != null) q.set('n_bins', String(nBins));
  return apiGet(P(`/doe/analysis/main-effects?${q.toString()}`));
}

export async function getInteraction(
  metricKey: string,
  factorA?: string,
  factorB?: string,
  nBins?: number
): Promise<{ factor_a: string; factor_b: string; matrix: (number | null)[][]; levels_a: number[]; levels_b: number[] }> {
  const q = new URLSearchParams();
  q.set('metric_key', metricKey);
  if (factorA) q.set('factor_a', factorA);
  if (factorB) q.set('factor_b', factorB);
  if (nBins != null) q.set('n_bins', String(nBins));
  return apiGet(P(`/doe/analysis/interaction?${q.toString()}`));
}

export async function getImportance(metricKey: string, factorKeys?: string): Promise<{ metric_key: string; importance: ImportanceItem[] }> {
  const q = new URLSearchParams();
  q.set('metric_key', metricKey);
  if (factorKeys) q.set('factor_keys', factorKeys);
  return apiGet(P(`/doe/analysis/importance?${q.toString()}`));
}
