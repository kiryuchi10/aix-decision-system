"""
Load and inspect .mat files (MACHINE_Data.mat, RFM_DATA.mat, OES_DATA.mat).
Uses scipy.io.loadmat. Typed and documented for use in notebooks and backend.
"""
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

def load_mat(filepath: str | Path) -> Dict[str, Any]:
    """
    Load a .mat file and return a dict of arrays/variables.
    """
    try:
        from scipy.io import loadmat as _loadmat
    except ImportError:
        raise ImportError("scipy is required: pip install scipy")
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(str(path))
    raw = _loadmat(str(path), struct_as_record=False, squeeze_me=True)
    # Drop MATLAB meta keys
    return {k: v for k, v in raw.items() if not k.startswith("__")}


def inspect_mat(filepath: str | Path) -> Dict[str, Any]:
    """
    Inspect keys and structure of a .mat file (shapes, dtypes).
    Returns a small dict suitable for inventory.
    """
    data = load_mat(filepath)
    out: Dict[str, Any] = {}
    for k, v in data.items():
        try:
            import numpy as np
            if hasattr(v, "shape"):
                out[k] = {"shape": getattr(v, "shape"), "dtype": getattr(v, "dtype", None)}
            elif isinstance(v, (list, tuple)):
                out[k] = {"type": type(v).__name__, "len": len(v)}
            else:
                out[k] = {"type": type(v).__name__}
        except Exception:
            out[k] = {"type": type(v).__name__}
    return out
