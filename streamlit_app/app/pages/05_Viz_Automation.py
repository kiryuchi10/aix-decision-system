"""
05 Viz Automation (8-Step)
Raw → Clean → EDA → FE → PCA → Cluster → Models → Policy
Each step: "Run step" runs pipeline → writes png/csv/json to reports/figures and data/processed.
Page renders from those artifacts (img + tables).
"""

import streamlit as st
from pathlib import Path
import sys

# Add parent so app.components and pipelines are findable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

STEPS = [
    "raw", "clean", "eda", "fe", "pca", "cluster", "models", "policy"
]

def main():
    st.title("Viz Automation (8-Step)")
    st.caption("Run step → artifacts in reports/figures and data/processed. Render from artifacts. No mock.")

    dataset_id = st.text_input("Dataset ID (or path to CSV)", value="1")
    step = st.selectbox("Step", STEPS)

    if st.button("Run step"):
        try:
            from pipelines.run_step import run_step
            base = Path(__file__).resolve().parent.parent.parent
            csv_path = base / "data" / "raw" / "sample.csv"
            if not csv_path.exists():
                csv_path = base / "data" / "processed" / dataset_id / "clean" / "cleaned.csv"
            if not csv_path.exists():
                st.warning("No CSV found. Add data/raw/sample.csv or run clean first.")
            else:
                result = run_step(dataset_id, step, str(csv_path))
                st.json(result)
                if result.get("status") == "ok":
                    st.success("Step completed. Artifacts written.")
        except Exception as e:
            st.exception(e)

    st.subheader("Artifacts")
    try:
        from app.components.artifact_grid import render_artifact_grid
        render_artifact_grid(dataset_id, step)
    except ImportError:
        figs = Path("reports/figures") / str(dataset_id) / step
        if figs.exists():
            for f in figs.glob("*.png"):
                st.image(str(f), caption=f.name)
        else:
            st.info("No artifacts yet. Run a step above.")


main()
