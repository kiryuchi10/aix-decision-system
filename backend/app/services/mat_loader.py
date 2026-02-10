"""
Generic .mat → DataFrame loader for diverse structures.
Use for seed-based EDA when LAM struct (calibration/test/variables) is not required.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import numpy as np
import pandas as pd


def _to_dataframe_from_mat(mat: Dict[str, Any]) -> pd.DataFrame:
    """
    Convert .mat dict to DataFrame defensively.
    - Case 1: key "data"/"Data"/"X"/"table" with 2D numeric array
    - Case 2: struct array (np.void with dtype.names)
    - Case 3: largest 2D numeric array
    """
    for key in ("data", "Data", "X", "table"):
        if key in mat and isinstance(mat[key], np.ndarray) and mat[key].ndim == 2:
            return pd.DataFrame(np.asarray(mat[key]))

    for k, v in mat.items():
        if k.startswith("__"):
            continue
        if isinstance(v, np.ndarray) and getattr(v.dtype, "names", None):
            cols = {}
            for name in v.dtype.names:
                col = np.squeeze(v[name])
                cols[name] = col
            return pd.DataFrame(cols)

    best_key = None
    best_size = 0
    for k, v in mat.items():
        if k.startswith("__"):
            continue
        if isinstance(v, np.ndarray) and v.ndim == 2 and np.issubdtype(v.dtype, np.number):
            size = v.shape[0] * v.shape[1]
            if size > best_size:
                best_size = size
                best_key = k
    if best_key is None:
        raise ValueError("No usable 2D numeric array found in .mat")
    return pd.DataFrame(np.asarray(mat[best_key]))


def load_mat_to_df(mat_path: str | Path) -> pd.DataFrame:
    """Load .mat file and return a DataFrame. Replaces inf with NaN."""
    try:
        from scipy.io import loadmat
    except ImportError:
        raise ImportError("scipy is required: pip install scipy")

    path = Path(mat_path)
    if not path.exists():
        raise FileNotFoundError(str(path))

    raw = loadmat(str(path), struct_as_record=False, squeeze_me=True)
    mat = {k: v for k, v in raw.items() if not k.startswith("__")}
    df = _to_dataframe_from_mat(mat)
    df = df.replace([np.inf, -np.inf], np.nan)
    return df
