import { apiGet, apiPost, apiPut } from '../../app/apiClient';

export type ProcessWindowRow = {
  key: string;
  unit?: string;
  hardMin: number;
  hardMax: number;
  note?: string;
};

export type ProcessWindowResponse = {
  updatedAt?: string;
  rows: ProcessWindowRow[];
};

export type AlarmThresholds = {
  enableWeco: boolean;
  sigmaThreshold: number;
  ewmaLambda: number;
};

export function getProcessWindow() {
  return apiGet<ProcessWindowResponse>('/settings/process-window');
}

export function saveProcessWindow(payload: ProcessWindowResponse) {
  return apiPost<ProcessWindowResponse, { ok: boolean }>('/settings/process-window', payload);
}

export function getAlarmThresholds() {
  return apiGet<AlarmThresholds>('/settings/alarm-thresholds');
}

export function saveAlarmThresholds(payload: AlarmThresholds) {
  return apiPost<AlarmThresholds, { ok: boolean }>('/settings/alarm-thresholds', payload);
}

export type IntegrationConfig = {
  type: string;
  config_json?: Record<string, unknown> | null;
  updatedAt?: string | null;
};

export function getIntegrations() {
  return apiGet<IntegrationConfig[]>('/settings/integrations');
}

export function getIntegration(type: string) {
  return apiGet<IntegrationConfig>(`/settings/integrations/${encodeURIComponent(type)}`);
}

export function updateIntegration(type: string, config_json: Record<string, unknown>) {
  return apiPut<{ config_json: Record<string, unknown> }, { ok: boolean }>(
    `/settings/integrations/${encodeURIComponent(type)}`,
    { config_json }
  );
}
