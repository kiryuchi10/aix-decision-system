"""
Pipeline Service (Artifact-First)
Runs pipeline steps (raw/clean/eda/fe/pca/cluster/models/policy) via etchfdc.pipeline.
Writes png/csv/json to app/data/reports/figures/{dataset_id}/{step}/ and app/data/processed/.
"""

from __future__ import annotations

import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import asdict

import pandas as pd
import numpy as np

from app.etchfdc.pipeline.context import PipelineContext
from app.etchfdc.pipeline.artifacts import list_step_artifacts
from app.etchfdc.pipeline.dataset_table import (
    build_features_from_csv,
    build_features_from_mat_inventory,
)
from app.etchfdc.pipeline.steps import (
    run_raw_step,
    run_clean_step,
    run_eda_step,
    run_fe_step,
    run_pca_step,
    run_cluster_step,
    run_models_step,
    run_policy_step,
)

BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BACKEND_ROOT / "app" / "data"
VALID_STEPS = ("raw", "clean", "eda", "fe", "pca", "cluster", "models", "policy")


def _mat_feature_df(data_path: str) -> pd.DataFrame:
    """Build wafer-level feature DataFrame from .mat (LAM-style calibration/test/variables)."""
    from app.services.mat_reader import mat_to_wafer_feature_df
    return mat_to_wafer_feature_df(data_path, limit=5000)


def _path_rel_to_backend(p: Path) -> str:
    """Return path as app/data/... relative to backend root."""
    try:
        rel = p.relative_to(BACKEND_ROOT)
        return "app/data/" + rel.as_posix().replace("\\", "/")
    except ValueError:
        return str(p)


def run_step(
    dataset_id: str,
    step: str,
    csv_path: str,
) -> Dict[str, Any]:
    """
    Run a single pipeline step. csv_path can be .csv or .mat.
    Returns { status, step, artifacts: [{ type, path, name }], summary }.
    """
    if step not in VALID_STEPS:
        return {"status": "error", "error": f"Invalid step: {step}", "artifacts": []}

    if not os.path.exists(csv_path):
        return {"status": "error", "error": f"Data file not found: {csv_path}", "artifacts": []}

    ctx = PipelineContext(dataset_id=str(dataset_id), base_dir=DATA_DIR)
    source_path = Path(csv_path)
    is_mat = source_path.suffix.lower() == ".mat"

    inv_dict: Dict[str, Any] = {}
    X: Optional[pd.DataFrame] = None
    y: Optional[pd.Series] = None
    mat_kind = source_path.stem

    if is_mat:
        from app.services.mat_reader import load_mat, build_inventory
        mat = load_mat(csv_path)
        inv = build_inventory(mat, source_file=os.path.basename(csv_path))
        inv_dict = {"wafers": [asdict(w) for w in inv.wafers]}
        X, y = build_features_from_mat_inventory(inv_dict, mat_kind)
    else:
        X, y = build_features_from_csv(source_path)

    if X is not None and X.shape[0] == 0:
        return {"status": "error", "error": "No rows after loading", "artifacts": []}

    try:
        result: Dict[str, Any] = {}
        if step == "eda" and is_mat:
            # .mat EDA: wafer-level feature df -> summary + hist, correlation, PCA
            df = _mat_feature_df(csv_path)
            step_figures = ctx.step_figures_dir("eda")
            step_figures.mkdir(parents=True, exist_ok=True)
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            summary = {
                "row_count": int(len(df)),
                "n_features": int(df.shape[1]),
                "label_counts": df["label"].value_counts().astype(int).to_dict(),
            }
            summary_path = ctx.step_processed_dir("eda") / "summary.json"
            summary_path.parent.mkdir(parents=True, exist_ok=True)
            with open(summary_path, "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2)

            feat_cols = [c for c in df.columns if c.endswith("__mean")]
            top = feat_cols[:12]

            # 1) hist grid (calib vs test)
            fig, axes = plt.subplots(3, 4, figsize=(14, 9))
            axes = axes.flatten()
            for i, col in enumerate(top):
                ax = axes[i]
                x0 = df[df["label"] == 0][col].dropna().values
                x1 = df[df["label"] == 1][col].dropna().values
                ax.hist(x0, bins=30, alpha=0.6, label="calib(0)")
                ax.hist(x1, bins=30, alpha=0.6, label="test(1)")
                ax.set_title(col.replace("__mean", ""), fontsize=9)
            axes[0].legend(fontsize=8)
            plt.tight_layout()
            out_hist = step_figures / "eda_hist_means.png"
            plt.savefig(out_hist, dpi=120)
            plt.close()

            # 2) correlation heatmap (top 30)
            use_cols = feat_cols[:30]
            corr = df[use_cols].corr(numeric_only=True).values
            fig, ax = plt.subplots(figsize=(10, 8))
            im = ax.imshow(corr, aspect="auto")
            ax.set_title("Correlation (mean features)")
            plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
            out_corr = step_figures / "eda_corr_heatmap.png"
            plt.tight_layout()
            plt.savefig(out_corr, dpi=120)
            plt.close()

            # 3) PCA scatter
            from sklearn.preprocessing import StandardScaler
            from sklearn.decomposition import PCA
            X_eda = df[feat_cols].fillna(0.0).values
            Xs = StandardScaler().fit_transform(X_eda)
            Z = PCA(n_components=2, random_state=0).fit_transform(Xs)
            fig, ax = plt.subplots(figsize=(8, 6))
            y = df["label"].values
            ax.scatter(Z[y == 0, 0], Z[y == 0, 1], s=15, alpha=0.7, label="calib(0)")
            ax.scatter(Z[y == 1, 0], Z[y == 1, 1], s=15, alpha=0.7, label="test(1)")
            ax.set_xlabel("PC1")
            ax.set_ylabel("PC2")
            ax.set_title("PCA (mean features)")
            ax.legend()
            out_pca = step_figures / "eda_pca_scatter.png"
            plt.tight_layout()
            plt.savefig(out_pca, dpi=120)
            plt.close()

            artifacts = list_step_artifacts(DATA_DIR, str(dataset_id), step)
            artifact_list = [{"type": a["type"], "path": a["path"], "name": a["name"]} for a in artifacts]
            return {
                "status": "ok",
                "step": step,
                "artifacts": artifact_list,
                "summary": {"step": step, "row_count": len(df), "artifact_count": len(artifact_list)},
            }

        if step == "raw":
            result = run_raw_step(ctx, inventory=inv_dict if inv_dict else {"wafers": []})
        elif step == "clean":
            result = run_clean_step(ctx, X)
        else:
            clean_path = ctx.step_processed_dir("clean") / "X_clean.parquet"
            if not clean_path.exists():
                run_clean_step(ctx, X)
            X_clean = pd.read_parquet(clean_path)

            if step == "eda":
                result = run_eda_step(ctx, X_clean)
            elif step == "fe":
                result = run_fe_step(ctx, X_clean)
            else:
                feat_path = ctx.step_processed_dir("fe") / "X_features.parquet"
                if not feat_path.exists():
                    run_fe_step(ctx, X_clean)
                X_feat = pd.read_parquet(feat_path)

                if step == "pca":
                    result = run_pca_step(ctx, X_feat)
                elif step == "cluster":
                    result = run_cluster_step(ctx, X_feat)
                elif step == "models":
                    result = run_models_step(ctx, X_feat, y)
                elif step == "policy":
                    pca_scores_path = ctx.step_processed_dir("pca") / "pca_scores.csv"
                    if pca_scores_path.exists():
                        Z = pd.read_csv(pca_scores_path).values
                        scores = Z[:, 0] if Z.shape[1] else np.zeros((X_feat.shape[0],))
                    else:
                        scores = X_feat.mean(axis=1).values
                    result = run_policy_step(ctx, scores)
                else:
                    return {"status": "error", "error": f"Unknown step: {step}", "artifacts": []}

        artifacts = list_step_artifacts(DATA_DIR, str(dataset_id), step)
        # Normalize to { type, path, name } for API (path already app/data/...)
        artifact_list = [{"type": a["type"], "path": a["path"], "name": a["name"]} for a in artifacts]
        row_count = result.get("row_count") or (len(X) if X is not None else 0)
        summary = {
            "step": step,
            "row_count": row_count,
            "artifact_count": len(artifact_list),
        }
        return {"status": "ok", "step": step, "artifacts": artifact_list, "summary": summary}
    except Exception as e:
        return {"status": "error", "error": str(e), "step": step, "artifacts": [], "summary": {"step": step, "row_count": 0, "artifact_count": 0}}


def list_artifacts(dataset_id: str, step: Optional[str] = None) -> List[Dict[str, str]]:
    """List artifacts for dataset_id; path is relative to backend root (app/data/...)."""
    raw = list_step_artifacts(DATA_DIR, str(dataset_id), step)
    return [{"type": a["type"], "path": a["path"], "name": a["name"]} for a in raw]


def get_summary(dataset_id: str, step: Optional[str] = None) -> Dict[str, Any]:
    """Get summary for dataset (and optional step)."""
    artifacts = list_artifacts(dataset_id, step)
    row_count = 0
    processed_dir = DATA_DIR / "processed" / str(dataset_id)
    if processed_dir.exists():
        inv_path = processed_dir / "raw" / "inventory.json"
        if inv_path.exists():
            try:
                data = json.loads(inv_path.read_text(encoding="utf-8"))
                row_count = len(data.get("wafers", []))
            except Exception:
                pass
        if row_count == 0:
            clean_path = processed_dir / "clean" / "X_clean.parquet"
            if clean_path.exists():
                try:
                    df = pd.read_parquet(clean_path, columns=[])
                    row_count = len(df)
                except Exception:
                    pass
    return {"dataset_id": dataset_id, "step": step, "row_count": row_count, "artifacts": artifacts}
