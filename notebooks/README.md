# Etch FDC Notebooks

Starter notebooks that load and process `.mat` files (MACHINE_Data.mat, RFM_DATA.mat, OES_DATA.mat) into standardized artifacts for the Viz Automation page.

## Input files

Place under `data/raw/` (relative to repo root or set `DATA_RAW` in notebooks):

- `MACHINE_Data.mat`
- `RFM_DATA.mat`
- `OES_DATA.mat`

You can copy from `backend/app/data/seed/process_etch/`:

```bash
mkdir -p data/raw
cp backend/app/data/seed/process_etch/*.mat data/raw/
```

## How to run notebooks and generate artifacts

1. **Environment**

   ```bash
   cd aix-decision-system
   python -m venv .venv
   source .venv/bin/activate   # or .venv\Scripts\activate on Windows
   pip install numpy pandas scipy scikit-learn matplotlib
   ```

2. **Run in order**

   | Notebook | Output |
   |----------|--------|
   | `01_load_mat_and_inventory.ipynb` | `data/interim/inventory.parquet` |
   | `02_build_long_table_timeseries.ipynb` | `data/interim/timeseries_long.parquet` |
   | `03_clean_align_resample.ipynb` | `data/processed/timeseries_resampled.npz` |
   | `04_feature_engineering_stats_fft.ipynb` | `data/processed/features_tabular.parquet` |
   | `05_pca_fdc_and_clustering.ipynb` | `data/processed/embeddings.parquet`, `cluster_labels.parquet`, `reports/figures/pca_*.png`, `cluster_*.png` |
   | `06_models_threshold_policy.ipynb` | `data/processed/predictions.parquet`, `docs/THRESHOLD_POLICY.md`, `reports/figures/*.png` |

3. **Paths**

   Run from repo root so that `data/raw`, `data/interim`, `data/processed`, and `reports/figures` resolve. Or set at the top of each notebook:

   ```python
   import sys
   sys.path.insert(0, "backend")
   from app.etchfdc.io.mat_reader import load_mat, inspect_mat
   ```

4. **Viz Automation**

   The Viz Automation page expects pipeline steps: Raw → Cleaning/Alignment → EDA → Feature Engineering → PCA/Embedding → Clustering → AI Models → Threshold/Policy (R/Y/G). Artifacts from these notebooks align with those steps (interim/processed parquet and figures).
