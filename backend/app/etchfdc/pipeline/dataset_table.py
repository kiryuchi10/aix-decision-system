# backend/app/etchfdc/pipeline/dataset_table.py
from __future__ import annotations
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
import pandas as pd


def _numeric_df(df: pd.DataFrame) -> pd.DataFrame:
    num = df.select_dtypes(include=["number"]).copy()
    num = num.dropna(axis=1, how="all")
    return num


def build_features_from_csv(csv_path: Path) -> Tuple[pd.DataFrame, Optional[pd.Series]]:
    df = pd.read_csv(csv_path)
    X = _numeric_df(df)
    y = None
    for col in ("label", "fault", "is_fault", "target", "y"):
        if col in df.columns:
            y = df[col]
            break
    return X, y


def build_features_from_mat_inventory(
    inv: Dict[str, Any], mat_kind: str
) -> Tuple[pd.DataFrame, pd.Series]:
    """
    inv must include wafers list with shape, label, exp_id (e.g. from DatasetInventory asdict).
    Returns feature matrix from shape stats + exp_id; labels from label (normal=0, fault=1).
    """
    wafers = inv.get("wafers", []) or []
    rows = []
    labels = []
    for w in wafers:
        shape = w.get("shape") or []
        tdim = int(shape[0]) if len(shape) > 0 else 0
        vdim = int(shape[1]) if len(shape) > 1 else 0
        rows.append({
            "tdim": tdim,
            "vdim": vdim,
            "nan_count": int(w.get("nan_count") or 0),
            "exp_id": int(w.get("exp_id") or 0),
            "source_kind": 1 if mat_kind.lower().startswith("machine") else 2 if mat_kind.lower().startswith("rfm") else 3,
        })
        labels.append(0 if (w.get("label") == "normal") else 1)
    X = pd.DataFrame(rows)
    y = pd.Series(labels, name="y")
    return X, y
