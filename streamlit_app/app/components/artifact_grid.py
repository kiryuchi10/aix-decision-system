"""Artifact grid: render png/csv/json from reports/figures and data/processed."""

import streamlit as st
from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent.parent

def render_artifact_grid(dataset_id: str, step: str = None):
    """List and render artifacts for dataset_id and optional step."""
    figures = ROOT / "reports" / "figures" / str(dataset_id)
    processed = ROOT / "data" / "processed" / str(dataset_id)
    for base in (figures, processed):
        if not base.exists():
            continue
        steps = [step] if step else [d.name for d in base.iterdir() if d.is_dir()]
        for s in steps:
            sub = base / s
            if not sub.exists():
                continue
            for f in sorted(sub.iterdir()):
                if not f.is_file():
                    continue
                if f.suffix.lower() in (".png", ".jpg", ".jpeg"):
                    st.image(str(f), caption=f.name)
                elif f.suffix.lower() == ".csv":
                    try:
                        df = pd.read_csv(f, nrows=100)
                        st.dataframe(df)
                    except Exception:
                        st.code(f.read_text())
                elif f.suffix.lower() == ".json":
                    try:
                        st.json(json.loads(f.read_text()))
                    except Exception:
                        st.code(f.read_text())
