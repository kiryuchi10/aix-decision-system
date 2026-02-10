"""
Pipeline run_step: run a single step (raw/clean/eda/fe/pca/cluster/models/policy).
Writes png/csv/json to reports/figures/{dataset_id}/{step}/ and data/processed/{dataset_id}/{step}/.
Can be called from Streamlit or from FastAPI backend (same logic).
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any

ROOT = Path(__file__).resolve().parent.parent
REPORTS_FIGURES = ROOT / "reports" / "figures"
DATA_PROCESSED = ROOT / "data" / "processed"
VALID_STEPS = ("raw", "clean", "eda", "fe", "pca", "cluster", "models", "policy")


def run_step(dataset_id: str, step: str, csv_path: str) -> Dict[str, Any]:
    """
    Run pipeline step. csv_path = path to source CSV.
    Returns { status, step, artifacts: [{ type, path, name }], summary }.
    """
    if step not in VALID_STEPS:
        return {"status": "error", "error": f"Invalid step: {step}", "artifacts": []}

    figures_dir = REPORTS_FIGURES / str(dataset_id) / step
    processed_dir = DATA_PROCESSED / str(dataset_id) / step
    figures_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    artifacts: List[Dict[str, str]] = []
    summary: Dict[str, Any] = {"step": step, "row_count": 0, "artifact_count": 0}

    if not os.path.exists(csv_path):
        return {"status": "error", "error": f"File not found: {csv_path}", "artifacts": []}

    try:
        import pandas as pd
        df = pd.read_csv(csv_path, nrows=10000)
    except Exception as e:
        return {"status": "error", "error": str(e), "artifacts": []}

    try:
        if step == "raw":
            out = processed_dir / "raw_summary.json"
            with open(out, "w") as f:
                json.dump({"rows": len(df), "columns": list(df.columns)}, f, indent=2)
            artifacts.append({"type": "json", "path": str(out), "name": "raw_summary.json"})

        elif step == "clean":
            df_clean = df.dropna(axis=0, how="all").dropna(axis=1, how="all")
            out_csv = processed_dir / "cleaned.csv"
            df_clean.to_csv(out_csv, index=False)
            artifacts.append({"type": "csv", "path": str(out_csv), "name": "cleaned.csv"})
            out_json = processed_dir / "clean_summary.json"
            with open(out_json, "w") as f:
                json.dump({"rows": len(df_clean), "columns": list(df_clean.columns)}, f, indent=2)
            artifacts.append({"type": "json", "path": str(out_json), "name": "clean_summary.json"})

        elif step == "eda":
            out_json = figures_dir / "eda_stats.json"
            with open(out_json, "w") as f:
                json.dump(df.describe().to_dict() if len(df) > 0 else {}, f, indent=2)
            artifacts.append({"type": "json", "path": str(out_json), "name": "eda_stats.json"})

        else:
            out_json = processed_dir / f"{step}_output.json"
            with open(out_json, "w") as f:
                json.dump({"step": step, "rows": len(df)}, f, indent=2)
            artifacts.append({"type": "json", "path": str(out_json), "name": f"{step}_output.json"})

        summary["row_count"] = len(df)
        summary["artifact_count"] = len(artifacts)
        return {"status": "ok", "step": step, "artifacts": artifacts, "summary": summary}

    except Exception as e:
        return {"status": "error", "error": str(e), "step": step, "artifacts": [], "summary": summary}
