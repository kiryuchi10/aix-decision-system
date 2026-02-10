# RCA Defect Prediction — Streamlit (A용)

Multipage Streamlit app. **No mock** — use real CSV/model artifacts from `data/` and `models/`.

## Directory structure

```
streamlit_app/
├── app/
│   ├── dashboard.py          # Entry: streamlit run app/dashboard.py
│   ├── pages/
│   │   ├── 01_Overview.py    # KPI + GO/WATCH/NO-GO + Top3 causes
│   │   ├── 02_RCA_Explorer.py
│   │   ├── 03_Predictions.py
│   │   ├── 04_Cost_Impact.py
│   │   └── 05_Viz_Automation.py  # 8-step, Run step → artifacts
│   └── components/
│       ├── kpi_cards.py
│       ├── filters_bar.py
│       ├── artifact_grid.py   # png/csv render from reports/figures
│       └── tables.py
├── pipelines/
│   └── run_step.py           # raw|clean|eda|fe|pca|cluster|models|policy
├── data/
│   ├── raw/
│   ├── interim/
│   └── processed/
├── models/
├── reports/
│   └── figures/              # {dataset_id}/{step}/*.png, *.csv, *.json
└── README.md
```

## Run

From `streamlit_app/`:

```bash
pip install streamlit pandas
streamlit run app/dashboard.py
```

## Artifact-first flow

1. Put CSV in `data/raw/` (or use DataHub in React app and sync).
2. In **05 Viz Automation**, set Dataset ID, choose step, click **Run step**.
3. `pipelines/run_step.py` writes to `reports/figures/{id}/{step}/` and `data/processed/{id}/{step}/`.
4. Pages render from those artifacts (img + tables). No Recharts/Plotly needed for static figures.

## Migration to React+FastAPI (B용)

Same `run_step` logic lives in `backend/app/services/pipeline_service.py`. Frontend calls:

- `POST /api/v1/viz/{id}/run-step?step=...`
- `GET /api/v1/viz/{id}/artifacts?step=...`
- `<img src="/api/v1/viz/artifacts/app/data/reports/figures/...">`
