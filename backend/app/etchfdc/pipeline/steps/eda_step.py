# backend/app/etchfdc/pipeline/steps/eda_step.py
from __future__ import annotations
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def run_eda_step(ctx, X_clean: pd.DataFrame) -> dict:
    sp = ctx.step_processed_dir("eda")
    figdir = ctx.step_figures_dir("eda")

    corr = X_clean.corr(numeric_only=True)
    plt.figure(figsize=(7, 6))
    plt.title("Correlation heatmap")
    plt.imshow(corr.values, aspect="auto")
    plt.colorbar()
    plt.tight_layout()
    plt.savefig(figdir / "corr.png", dpi=150)
    plt.close()

    cols = X_clean.columns[:3].tolist()
    plt.figure(figsize=(8, 4))
    plt.title("Distributions (first 3 features)")
    for c in cols:
        plt.hist(X_clean[c].values, bins=30, alpha=0.5, label=str(c))
    plt.legend()
    plt.tight_layout()
    plt.savefig(figdir / "dist.png", dpi=150)
    plt.close()

    return {"artifacts": ["corr.png", "dist.png"]}
