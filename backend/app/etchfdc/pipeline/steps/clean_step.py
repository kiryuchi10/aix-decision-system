# backend/app/etchfdc/pipeline/steps/clean_step.py
from __future__ import annotations
from typing import Dict, Any
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler


def run_clean_step(ctx, X: pd.DataFrame) -> Dict[str, Any]:
    sp = ctx.step_processed_dir("clean")
    figdir = ctx.step_figures_dir("clean")

    miss = X.isna().mean().sort_values(ascending=False).head(20)

    plt.figure(figsize=(8, 4))
    plt.title("Top missing ratio (before clean)")
    if len(miss) > 0:
        plt.bar(miss.index.astype(str), miss.values)
    plt.xticks(rotation=60, ha="right")
    plt.tight_layout()
    plt.savefig(figdir / "missing_before.png", dpi=150)
    plt.close()

    imputer = SimpleImputer(strategy="median")
    scaler = StandardScaler()
    X_imp = pd.DataFrame(imputer.fit_transform(X), columns=X.columns)
    X_scaled = pd.DataFrame(scaler.fit_transform(X_imp), columns=X.columns)
    X_scaled.to_parquet(sp / "X_clean.parquet", index=False)

    plt.figure(figsize=(8, 4))
    plt.title("Missing ratio (after clean)")
    plt.bar(["all"], [0.0])
    plt.tight_layout()
    plt.savefig(figdir / "missing_after.png", dpi=150)
    plt.close()

    return {"row_count": int(X.shape[0]), "artifacts": ["missing_before.png", "missing_after.png", "X_clean.parquet"]}
