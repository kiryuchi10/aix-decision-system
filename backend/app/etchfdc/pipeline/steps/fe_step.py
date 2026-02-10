# backend/app/etchfdc/pipeline/steps/fe_step.py
from __future__ import annotations
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def run_fe_step(ctx, X_clean: pd.DataFrame) -> dict:
    sp = ctx.step_processed_dir("fe")
    figdir = ctx.step_figures_dir("fe")

    var = X_clean.var().sort_values(ascending=False).head(20)
    plt.figure(figsize=(8, 4))
    plt.title("Top feature variance")
    plt.bar(var.index.astype(str), var.values)
    plt.xticks(rotation=60, ha="right")
    plt.tight_layout()
    plt.savefig(figdir / "feature_variance.png", dpi=150)
    plt.close()

    X_clean.to_parquet(sp / "X_features.parquet", index=False)
    return {"artifacts": ["feature_variance.png", "X_features.parquet"]}
