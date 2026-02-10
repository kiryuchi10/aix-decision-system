/**
 * Viz Automation + Datasets API (artifact-first, real fetch).
 * Uses same server root as apiClient; paths always go to /api/v1/...
 */

import { apiGet, apiPost } from '../../app/apiClient';

/** Server root for backend (e.g. http://localhost:8000). Used for health check and artifact URLs. */
export const VIZ_SERVER =
  ((import.meta.env.VITE_API_BASE_URL as string) || 'http://localhost:8000').replace(/\/$/, '');
const SERVER = VIZ_SERVER;
const BASE = SERVER.endsWith('/api/v1') ? SERVER : `${SERVER}/api/v1`;

export interface DatasetMeta {
  id: number;
  filename: string;
  row_count: number | null;
  column_count: number | null;
  stage?: string;
  committed: boolean;
  created_at: string;
}

export interface PreviewResponse {
  datasetId: number;
  stage: string;
  rowCount: number;
  columnCount: number;
  columns: string[] | { name: string; type?: string; description?: string; missingCount?: number }[];
  rows?: Record<string, unknown>[];
  wafersPreview?: { wafer_id: string; split: string; label: string; exp_id: number | null; fault_name: string | null; shape: number[] | null; nan_count: number | null }[];
  total_rows?: number;
}

export interface ArtifactItem {
  id: string;
  step: string;
  kind: string;
  title: string;
  url: string;
  createdAt: string;
}

export interface StepSummary {
  dataset_id: string;
  step: string | null;
  row_count: number;
  artifacts: { type: string; path: string; name: string }[] | ArtifactItem[];
}

export function getDatasets(): Promise<DatasetMeta[]> {
  return apiGet<DatasetMeta[]>('/datasets');
}

export function uploadDataset(file: File): Promise<DatasetMeta> {
  const form = new FormData();
  form.append('file', file);
  const token = localStorage.getItem('token');
  return fetch(`${BASE}/datasets/upload`, {
    method: 'POST',
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: form,
  }).then(async (res) => {
    if (!res.ok) {
      const t = await res.text();
      throw new Error(t || `Upload failed: ${res.status}`);
    }
    return res.json();
  });
}

export function getPreview(datasetId: number, rows = 50): Promise<PreviewResponse> {
  return apiGet<PreviewResponse>(`/datasets/${datasetId}/preview?rows=${rows}`);
}

export function postPreview(datasetId: number, rows = 50): Promise<PreviewResponse> {
  return apiPost<unknown, PreviewResponse>(`/datasets/${datasetId}/preview?rows=${rows}`, {});
}

export function undoPreview(datasetId: number): Promise<{ ok: boolean; message: string; stage?: string }> {
  return apiPost<unknown, { ok: boolean; message: string; stage?: string }>(`/datasets/${datasetId}/undo-preview`, {});
}

export function commitDataset(datasetId: number): Promise<{ ok: boolean; message: string; dataset_id: number; stage?: string }> {
  return apiPost<unknown, { ok: boolean; message: string; dataset_id: number; stage?: string }>(`/datasets/${datasetId}/commit`, {});
}

export function getVizSummary(datasetId: number, step?: string): Promise<StepSummary> {
  const q = step ? `?step=${encodeURIComponent(step)}` : '';
  return apiGet<StepSummary>(`/viz/${datasetId}/summary${q}`);
}

export function getVizArtifacts(datasetId: number, step?: string): Promise<{ dataset_id: number; step: string | null; artifacts: ArtifactItem[] }> {
  const q = step ? `?step=${encodeURIComponent(step)}` : '';
  return apiGet<{ dataset_id: number; step: string | null; artifacts: ArtifactItem[] }>(`/viz/${datasetId}/artifacts${q}`);
}

export type EtchSource = 'MACHINE' | 'OES' | 'RFM';

export function runStep(
  datasetId: number,
  step: string,
  source?: EtchSource | null
): Promise<{ status: string; step: string; source?: string; artifacts?: unknown[]; summary?: unknown; error?: string; artifact_count?: number }> {
  const params = new URLSearchParams({ step });
  if (source) params.set('source', source);
  return apiPost<unknown, { status: string; step: string; source?: string; artifacts?: unknown[]; summary?: unknown; error?: string; artifact_count?: number }>(
    `/viz/${datasetId}/run-step?${params.toString()}`,
    {}
  );
}

/** Full URL for artifact image (for <img src>). Backend returns url like /api/v1/viz/artifacts/app/data/... */
export function artifactImageUrl(urlPath: string): string {
  if (urlPath.startsWith('http')) return urlPath;
  const path = urlPath.startsWith('/') ? urlPath : `/${urlPath}`;
  return `${SERVER}${path}`;
}

/** Check if backend is reachable (no auth). Use for Viz Automation connectivity message. */
export function checkBackendHealth(): Promise<boolean> {
  return fetch(`${BASE}/health`, { method: 'GET', credentials: 'omit' })
    .then((r) => r.ok)
    .catch(() => false);
}
