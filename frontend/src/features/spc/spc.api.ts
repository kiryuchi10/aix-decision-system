import { apiGet, apiPost } from '../../app/apiClient';

export type ChartRequest = {
  entity_type: string;
  entity_id: string;
  metric_name: string;
  chart_type?: string;
  subgroup_size?: number;
  data_range_hours?: number;
};

export type ChartResponse = {
  chart_type: string;
  mean: number;
  std_dev: number;
  ucl: number;
  lcl: number;
  cl: number;
  cp?: number | null;
  cpk?: number | null;
  data_points: Array<{ index: number; value: number; timestamp: string }>;
  violations: Array<{
    rule_number: number;
    rule_name: string;
    point_index: number;
    point_value: number;
    severity: string;
  }>;
};

export type ViolationResponse = {
  id: number;
  rule_number: number;
  rule_name: string;
  violation_type: string;
  point_index: number;
  point_value: number;
  severity: string;
  status: string;
  detected_at: string;
};

export function postSpcChart(payload: ChartRequest) {
  return apiPost<ChartRequest, ChartResponse>('/spc/chart', payload);
}

export function getSpcViolations(rangeHours = 24, entityType?: string, entityId?: string) {
  const params = new URLSearchParams({ range_hours: String(rangeHours) });
  if (entityType) params.append('entity_type', entityType);
  if (entityId) params.append('entity_id', entityId);
  return apiGet<ViolationResponse[]>(`/spc/violations?${params.toString()}`);
}

export function getCpkTrend(entity: string, entityId?: string, metricName?: string, days = 30) {
  const params = new URLSearchParams({ entity, days: String(days) });
  if (entityId) params.append('entity_id', entityId);
  if (metricName) params.append('metric_name', metricName);
  return apiGet<Array<{
    timestamp: string;
    cpk: number;
    cp: number;
    mean: number;
    std_dev: number;
  }>>(`/spc/cpk-trend?${params.toString()}`);
}
