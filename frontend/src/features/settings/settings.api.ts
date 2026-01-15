import { apiGet, apiPost } from '../../app/apiClient';

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
