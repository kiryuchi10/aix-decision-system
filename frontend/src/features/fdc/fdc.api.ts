import { apiGet, apiPost } from '../../app/apiClient';

export type Alarm = {
  id: string;
  timestamp: string;
  severity: string;
  type: string;
  parameter: string;
  current_value: number;
  threshold_value: number;
  sigma_distance: number;
  yield_impact: number;
  status: string;
};

export type ProcessCapability = {
  cpk: number;
  cp: number;
  drift_rate: number;
  yield_estimate: number;
};

export function getActiveAlarms() {
  return apiGet<Alarm[]>('/fdc/alarms/active');
}

export function getFdcProcessCapability() {
  return apiGet<ProcessCapability>('/fdc/process-capability');
}

export function acknowledgeAlarm(alarmId: string) {
  return apiPost<{}, { message: string }>(`/fdc/alarms/${alarmId}/ack`, {});
}

export function resolveAlarm(alarmId: string) {
  return apiPost<{}, { message: string }>(`/fdc/alarms/${alarmId}/resolve`, {});
}
