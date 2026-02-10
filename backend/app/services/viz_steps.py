"""
Viz pipeline step runners for seed-based EDA.
Produces summary + PNG artifacts (NaN bar, correlation heatmap) from any numeric DataFrame.
"""
from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def run_eda_step(df: pd.DataFrame, source: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    EDA summary + PNG artifacts from loaded DataFrame.
    - summary: shape, nan_ratio, top_nan_cols, describe
    - artifacts: list of { kind, name, bytes }
    """
    numeric = df.select_dtypes(include=[np.number]).copy()
    numeric = numeric.replace([np.inf, -np.inf], np.nan)

    summary: Dict[str, Any] = {
        "source": source,
        "shape": [int(numeric.shape[0]), int(numeric.shape[1])],
        "nan_ratio": float(numeric.isna().mean().mean()) if numeric.size else 0.0,
    }

    nan_by_col = numeric.isna().mean().sort_values(ascending=False).head(10)
    summary["top_nan_cols"] = [{"col": c, "nan_ratio": float(r)} for c, r in nan_by_col.items()]

    try:
        desc = numeric.describe(include="all")
        summary["describe"] = {str(c): desc[c].dropna().astype(float).tolist() for c in desc.columns}
    except Exception:
        summary["describe"] = {}

    artifacts: List[Dict[str, Any]] = []

    # Plot 1: Top NaN columns bar
    if len(nan_by_col) > 0:
        buf = io.BytesIO()
        fig, ax = plt.subplots(figsize=(8, 4))
        nan_by_col.plot(kind="bar", ax=ax)
        ax.set_title(f"[{source}] Top NaN Columns")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        plt.savefig(buf, format="png", dpi=120)
        plt.close()
        artifacts.append({"kind": "png", "name": f"eda_nan_{source}.png", "bytes": buf.getvalue()})

    # Plot 2: Correlation heatmap (up to 25 cols)
    cols = list(numeric.columns)[:25]
    if len(cols) >= 2:
        corr = numeric[cols].corr()
        buf = io.BytesIO()
        fig, ax = plt.subplots(figsize=(10, 8))
        im = ax.imshow(corr.values, aspect="auto", vmin=-1, vmax=1)
        ax.set_title(f"[{source}] Correlation (first {len(cols)} cols)")
        ax.set_xticks(range(len(cols)))
        ax.set_xticklabels(cols, rotation=90, fontsize=6)
        ax.set_yticks(range(len(cols)))
        ax.set_yticklabels(cols, fontsize=6)
        plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        plt.tight_layout()
        plt.savefig(buf, format="png", dpi=120)
        plt.close()
        artifacts.append({"kind": "png", "name": f"eda_corr_{source}.png", "bytes": buf.getvalue()})

    return summary, artifacts


def save_artifacts_for_step(
    dataset_id: int,
    step: str,
    source: str,
    summary: Dict[str, Any],
    artifacts: List[Dict[str, Any]],
    base_dir: Path,
) -> None:
    """
    Write summary.json and PNGs to base_dir/reports/preview/{dataset_id}/{step}/{source}/.
    """
    out_dir = base_dir / "app" / "data" / "reports" / "preview" / str(dataset_id) / step / source
    out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    for a in artifacts:
        if a.get("kind") == "png" and "bytes" in a:
            (out_dir / a["name"]).write_bytes(a["bytes"])


def list_preview_artifacts(base_dir: Path, dataset_id: int, step: str, source: str) -> List[Dict[str, str]]:
    """List files in preview/{dataset_id}/{step}/{source}/ as { type, path, name }. path is relative to base_dir for URL."""
    out_dir = base_dir / "app" / "data" / "reports" / "preview" / str(dataset_id) / step / source
    result = []
    if not out_dir.exists():
        return result
    for p in sorted(out_dir.iterdir()):
        if not p.is_file():
            continue
        suffix = p.suffix.lower()
        kind = "png" if suffix in (".png", ".jpg", ".jpeg") else "json" if suffix == ".json" else "file"
        try:
            rel = p.relative_to(base_dir)
            path_str = rel.as_posix().replace("\\", "/")
        except ValueError:
            path_str = str(p)
        result.append({"type": kind, "path": path_str, "name": p.name})
    return result
