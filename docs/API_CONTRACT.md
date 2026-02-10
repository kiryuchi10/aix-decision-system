# AiX Decision System — API Contract (Artifact-First, Real Data)

RCA + Defect Prediction → Operational decision (GO / WATCH / NO-GO). No mock; all endpoints use real datasets and artifacts (png/csv/json).

---

## Base URL

- Development: `http://localhost:8000/api/v1`
- All requests (except login/signup) require `Authorization: Bearer <token>`.

---

## 1. Datasets (DataHub)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/datasets` | List datasets (include `stage`, `committed`) |
| POST | `/datasets/upload` | Upload CSV or .mat (creates in DRAFT) |
| GET | `/datasets/{id}` | Get dataset metadata (columns/meta from inventory when available) |
| GET | `/datasets/{id}/preview?rows=50` | Get preview (from stored JSON if stage=PREVIEW, else on the fly) |
| POST | `/datasets/{id}/preview?rows=50` | Parse inventory + write preview JSON to disk, set stage=PREVIEW |
| POST | `/datasets/{id}/undo-preview` | Delete preview artifacts, set stage=DRAFT |
| POST | `/datasets/{id}/commit` | Set stage=COMMITTED, committed=true (pipeline can run) |

**DatasetMeta (list/detail)**

- `id`, `filename`, `row_count`, `column_count`, `stage` (DRAFT | PREVIEW | COMMITTED), `committed`, `created_at`, `storage_path?`, `schema_json?`

**Preview response**

- `datasetId`, `stage`, `rowCount`, `columnCount`, `columns` (list of names or `{ name, type, description, missingCount }`), `rows?` (CSV), `wafersPreview?` (wafer list for .mat: `wafer_id`, `split`, `label`, `exp_id`, `fault_name`, `shape`, `nan_count`), `total_rows?`

---

## 2. Viz / Pipeline (Artifact-First)

Pipeline steps: `raw` | `clean` | `eda` | `fe` | `pca` | `cluster` | `models` | `policy`.

| Method | Path | Description |
|--------|------|-------------|
| POST | `/viz/{id}/run-step?step={step}` | Run step for dataset `id`. **Blocked with 403 if dataset.committed is false.** Writes png/csv/json. Returns `{ status, step, artifacts, summary }`. |
| GET | `/viz/{id}/summary?step={step}` | **StepSummary:** row_count, artifact count. |
| GET | `/viz/{id}/artifacts?step={step}` | List **Artifact:** `[{ id, step, kind, title, url, createdAt }]`. `url` for `<img src>`. |
| GET | `/viz/artifacts/{path:path}` | Serve artifact file (path relative to backend, e.g. `app/data/reports/figures/1/raw/heatmap.png`). |

**Artifact (example)**

- `id`, `step`, `kind` (png | csv | json), `title`, `url` (e.g. `/api/v1/viz/artifacts/app/data/reports/figures/1/raw/heatmap.png`), `createdAt`

**StepSummary (example)**

- `dataset_id`, `step`, `row_count`, `artifacts` (list)

---

## 3. RCA (Root Cause Explorer)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/rca/pareto?dimension=stage\|vendor\|error_code\|shift` | Pareto data for dimension (real from DB/processed). |
| GET | `/rca/drivers` | Driver candidates (correlation/regression-based). |
| GET | `/rca/clusters` | Similar-pattern groups (cluster ids + labels). |
| GET | `/rca/clusters/{id}/causes` | Top causes/actions for cluster. |

---

## 4. Prediction

| Method | Path | Description |
|--------|------|-------------|
| GET | `/prediction/risk-table` | Lot/unit risk table: probability, risk_level, top_drivers. |
| POST | `/prediction/calibrate` | Body: `{ threshold }`. Return suggested threshold. |
| GET | `/prediction/policy` | Current policy (threshold, GO/WATCH/NO-GO rules). |

---

## 5. Overview / Dashboard (GO-WATCH-NO-GO)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/dashboard/kpis` | Fail rate, top stage, top vendor, cost loss, alerts/day. |
| GET | `/dashboard/verdict` | GO / WATCH / NO-GO + reason. |
| GET | `/dashboard/top-causes` | Top 3 causes (Pareto + short reason). |

---

## 6. Cost Impact

| Method | Path | Description |
|--------|------|-------------|
| POST | `/cost/optimal-threshold` | Body: `{ fp_cost, fn_cost }` → recommended threshold. |
| GET | `/cost/alarm-volume` | Alarm volume/day (for charts). |

---

## 7. Auth

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/login` | Body: `{ username, password }` → `{ access_token, token_type }`. |
| POST | `/auth/signup` | Body: `{ email, password, full_name? }`. |
| GET | `/auth/me` | Current user (requires token). |

---

## Artifact-First Flow (No Mock)

1. **DataHub:** Upload → Preview → (optional Undo preview) → Commit.
2. **Viz Automation:** Select committed dataset → "Run step" (raw → clean → … → policy) → backend writes png/csv/json → frontend GET artifacts → show via `<img src>` and tables.
3. **Overview:** KPIs + verdict (GO/WATCH/NO-GO) + top causes from real data.
4. **RCA Explorer:** Pareto / drivers / clusters from processed data.
5. **Predictions:** Risk table + threshold slider (real model/artifacts).
6. **Cost Impact:** FP/FN cost input → optimal threshold; alarm volume from data.

---

## File Layout (Backend)

- `data/raw/` — uploaded/original.
- `data/interim/` — cleaned/intermediate.
- `data/processed/` — features, preds, CSVs/JSONs from pipeline.
- `reports/figures/{dataset_id}/{step}/` — step-wise png (and optional csv/json).
- `models/` — model.joblib, scaler.joblib, feature_columns.json.
