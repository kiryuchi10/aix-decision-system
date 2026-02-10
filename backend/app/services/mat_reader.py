"""
MAT loader + inventory builder for LAM 9600 etch FDC dataset.
Loads MACHINE_Data.mat / RFM_DATA.mat / OES_DATA.mat.
Extracts inventory: wafer list, split, label, exp_id, variable names, shapes.
Lightweight preview for backend APIs (no full arrays in JSON).
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

MatDict = Dict[str, Any]


def load_mat(filepath: Union[str, Path]) -> MatDict:
    """
    Load a .mat file and return a dict of arrays/variables.
    Uses scipy.io.loadmat with MATLAB-friendly options.
    """
    try:
        from scipy.io import loadmat as _loadmat
    except ImportError:
        raise ImportError("scipy is required: pip install scipy")

    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(str(path))

    raw = _loadmat(
        str(path),
        struct_as_record=False,
        squeeze_me=True,
        chars_as_strings=False,
    )
    return {k: v for k, v in raw.items() if not k.startswith("__")}


def _is_mat_struct(x: Any) -> bool:
    return hasattr(x, "_fieldnames")


def _mat_char_to_str(x: Any) -> Optional[str]:
    """Convert MATLAB char array or numpy scalar into python str."""
    if x is None:
        return None
    if isinstance(x, str):
        return x.strip()
    if isinstance(x, (bytes, np.bytes_)):
        try:
            return x.decode("utf-8", errors="ignore").strip()
        except Exception:
            return str(x).strip()
    if isinstance(x, np.ndarray):
        if x.dtype.kind in {"U", "S"}:
            if x.ndim == 0:
                return str(x.item()).strip()
            if x.ndim == 1:
                return "".join([str(c) for c in x.tolist()]).strip()
    return None


def _mat_char_matrix_to_list(x: Any) -> Optional[List[str]]:
    """Convert MATLAB char matrix (n x m) into list of strings."""
    if not isinstance(x, np.ndarray) or x.ndim != 2 or x.dtype.kind not in {"U", "S"}:
        return None
    out: List[str] = []
    for i in range(x.shape[0]):
        row = x[i, :]
        if row.dtype.kind == "S":
            s = b"".join(row.tolist()).decode("utf-8", errors="ignore")
        else:
            s = "".join(row.tolist())
        out.append(s.strip())
    return out


def _to_py(x: Any, *, max_list: int = 200) -> Any:
    """Recursively convert MATLAB-ish objects to python-native."""
    if _is_mat_struct(x):
        d: Dict[str, Any] = {}
        for f in getattr(x, "_fieldnames", []) or []:
            d[f] = _to_py(getattr(x, f), max_list=max_list)
        return d
    str_list = _mat_char_matrix_to_list(x)
    if str_list is not None:
        return str_list
    s = _mat_char_to_str(x)
    if s is not None:
        return s
    if isinstance(x, np.ndarray) and x.dtype == object:
        flat = x.ravel().tolist()
        if len(flat) > max_list:
            return [_to_py(v, max_list=max_list) for v in flat[:max_list]] + ["..."]
        return [_to_py(v, max_list=max_list) for v in flat]
    if isinstance(x, (list, tuple)):
        return [_to_py(v, max_list=max_list) for v in x[:max_list]]
    return x


@dataclass
class WaferMeta:
    wafer_id: str
    split: str  # "calib" | "test"
    label: str  # "normal" | "fault"
    exp_id: Optional[int]
    fault_name: Optional[str]
    shape: Optional[Tuple[int, ...]]
    nan_count: Optional[int]


@dataclass
class DatasetInventory:
    source_file: str
    n_calib: int
    n_test: int
    variables: List[str]
    wafers: List[WaferMeta]


def _extract_exp_id(name: str) -> Optional[int]:
    for exp in (29, 31, 33):
        if str(exp) in name:
            return exp
    return None


def build_inventory(mat: MatDict, *, source_file: str) -> DatasetInventory:
    """
    Build lightweight inventory for frontend preview.
    Expects struct with: calibration, calib_names, test, test_names, fault_names, variables.
    """
    candidate = None
    for k, v in mat.items():
        pv = _to_py(v)
        if isinstance(pv, dict) and {"calibration", "calib_names", "test", "test_names", "fault_names", "variables"} <= set(pv.keys()):
            candidate = pv
            break
    if candidate is None:
        candidate = _to_py(mat)

    calib_names = candidate.get("calib_names", []) or []
    test_names = candidate.get("test_names", []) or []
    fault_names = candidate.get("fault_names", []) or []
    variables = candidate.get("variables", []) or []
    if isinstance(variables, str):
        variables = [variables]
    variables = [str(v).strip() for v in variables if str(v).strip()]

    calibration = candidate.get("calibration", []) or []
    test = candidate.get("test", []) or []
    wafers: List[WaferMeta] = []

    def summarize_arr(a: Any) -> Tuple[Optional[Tuple[int, ...]], Optional[int]]:
        if isinstance(a, np.ndarray):
            shape = tuple(a.shape)
            if a.dtype.kind == "f":
                return shape, int(np.isnan(a).sum())
            return shape, None
        return None, None

    for i, name in enumerate(calib_names):
        wafer_id = str(name).strip()
        arr = calibration[i] if isinstance(calibration, list) and i < len(calibration) else None
        shape, nan_count = summarize_arr(arr)
        wafers.append(
            WaferMeta(
                wafer_id=wafer_id,
                split="calib",
                label="normal",
                exp_id=_extract_exp_id(wafer_id),
                fault_name=None,
                shape=shape,
                nan_count=nan_count,
            )
        )
    for i, name in enumerate(test_names):
        wafer_id = str(name).strip()
        arr = test[i] if isinstance(test, list) and i < len(test) else None
        shape, nan_count = summarize_arr(arr)
        fault = str(fault_names[i]).strip() if i < len(fault_names) else None
        wafers.append(
            WaferMeta(
                wafer_id=wafer_id,
                split="test",
                label="fault",
                exp_id=_extract_exp_id(wafer_id),
                fault_name=fault,
                shape=shape,
                nan_count=nan_count,
            )
        )

    return DatasetInventory(
        source_file=source_file,
        n_calib=len(calib_names),
        n_test=len(test_names),
        variables=variables,
        wafers=wafers,
    )


def _struct_to_cal_test_vars(mat: MatDict) -> Tuple[List[np.ndarray], List[np.ndarray], List[str], Optional[List[str]]]:
    """Extract calibration, test, variables, and optional fault_names from loaded .mat."""
    s = None
    for k, v in mat.items():
        if hasattr(v, "calibration") and hasattr(v, "test") and hasattr(v, "variables"):
            s = v
            break
    if s is None:
        pv = _to_py(next(iter(mat.values())) if mat else None)
        if isinstance(pv, dict) and "calibration" in pv and "test" in pv and "variables" in pv:
            cal = pv.get("calibration") or []
            test = pv.get("test") or []
            variables = pv.get("variables") or []
            fault_names = pv.get("fault_names") if isinstance(pv.get("fault_names"), list) else None
            if isinstance(variables, str):
                variables = [variables]
            variables = [str(x).strip() for x in variables if str(x).strip()]
            def to_arr_list(x: Any) -> List[np.ndarray]:
                if isinstance(x, np.ndarray) and x.dtype == object:
                    return [np.asarray(e, dtype=float) for e in x.ravel().tolist()]
                if isinstance(x, list):
                    return [np.asarray(e, dtype=float) for e in x]
                return []
            return to_arr_list(cal), to_arr_list(test), variables, fault_names
        raise ValueError("Unsupported .mat schema: need calibration, test, variables")
    cal = getattr(s, "calibration", None)
    test = getattr(s, "test", None)
    variables = getattr(s, "variables", None)
    fault_names = getattr(s, "fault_names", None) if hasattr(s, "fault_names") else None
    if cal is None or test is None or variables is None:
        raise ValueError("Unsupported .mat schema: need calibration, test, variables")
    if isinstance(cal, np.ndarray) and cal.dtype == object:
        cal_list = [np.asarray(x, dtype=float) for x in cal.ravel().tolist()]
    else:
        cal_list = [np.asarray(x, dtype=float) for x in (cal if isinstance(cal, list) else [])]
    if isinstance(test, np.ndarray) and test.dtype == object:
        test_list = [np.asarray(x, dtype=float) for x in test.ravel().tolist()]
    else:
        test_list = [np.asarray(x, dtype=float) for x in (test if isinstance(test, list) else [])]
    if isinstance(variables, np.ndarray):
        variables = variables.ravel().tolist()
    if isinstance(variables, str):
        variables = [variables]
    variables = [str(v).strip() for v in variables if str(v).strip()]
    fn_list: Optional[List[str]] = None
    if fault_names is not None:
        try:
            if isinstance(fault_names, np.ndarray):
                fn_list = [str(x).strip() for x in fault_names.ravel().tolist()]
            else:
                fn_list = [str(x).strip() for x in (fault_names if isinstance(fault_names, list) else [])]
        except Exception:
            fn_list = None
    return cal_list, test_list, variables, fn_list


def mat_to_wafer_feature_df(filepath: Union[str, Path], *, limit: int = 5000) -> "pd.DataFrame":
    """
    Build a wafer-level feature DataFrame (mean/std per variable) from LAM-style .mat.
    Returns DataFrame with columns: wafer_id, split, label, fault_name, {var}__mean, {var}__std.
    """
    import pandas as pd
    raw = load_mat(filepath)
    cal_list, test_list, variables, fault_names = _struct_to_cal_test_vars(raw)
    rows: List[Dict[str, Any]] = []

    def add_wafer(block: np.ndarray, wafer_id: str, split: str, label: int, fault_name: Optional[str] = None) -> None:
        x = np.asarray(block, dtype=float)
        mu = np.nanmean(x, axis=0)
        sd = np.nanstd(x, axis=0)
        r: Dict[str, Any] = {
            "wafer_id": wafer_id,
            "split": split,
            "label": int(label),
            "fault_name": (fault_name or ""),
        }
        for j, vname in enumerate(variables):
            r[f"{vname}__mean"] = float(mu[j]) if j < len(mu) else np.nan
            r[f"{vname}__std"] = float(sd[j]) if j < len(sd) else np.nan
        rows.append(r)

    n_cal = min(len(cal_list), limit)
    for i in range(n_cal):
        add_wafer(cal_list[i], f"CAL_{i:04d}", "calib", 0, None)
    remain = max(0, limit - n_cal)
    for i in range(min(len(test_list), remain)):
        fn = (fault_names[i] if fault_names and i < len(fault_names) else None) or ""
        add_wafer(test_list[i], f"TEST_{i:04d}", "test", 1, fn)

    return pd.DataFrame(rows)


def inspect_mat(filepath: Union[str, Path]) -> Dict[str, Any]:
    """Inspect keys/structure and emit dataset inventory if LAM 9600 etch structure."""
    mat = load_mat(filepath)
    out: Dict[str, Any] = {"keys": {}}
    for k, v in mat.items():
        if isinstance(v, np.ndarray) and v.dtype != object:
            out["keys"][k] = {"shape": tuple(v.shape), "dtype": str(v.dtype)}
        elif isinstance(v, np.ndarray) and v.dtype == object:
            out["keys"][k] = {"type": "object_array", "shape": tuple(v.shape)}
        else:
            out["keys"][k] = {"type": type(v).__name__}
    try:
        inv = build_inventory(mat, source_file=str(filepath))
        out["inventory"] = {
            "source_file": inv.source_file,
            "n_calib": inv.n_calib,
            "n_test": inv.n_test,
            "variables_count": len(inv.variables),
            "exp_counts": {
                "29": sum(1 for w in inv.wafers if w.exp_id == 29),
                "31": sum(1 for w in inv.wafers if w.exp_id == 31),
                "33": sum(1 for w in inv.wafers if w.exp_id == 33),
            },
            "wafers_preview": [asdict(w) for w in inv.wafers[:10]],
        }
    except Exception as e:
        out["inventory_error"] = str(e)
    return out
