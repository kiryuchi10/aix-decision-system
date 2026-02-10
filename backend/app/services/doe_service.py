# app/services/doe_service.py
"""DOE overlay points and analysis (main effects, interaction, importance) for VPD dashboard."""
import json
from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session
from app.models.doe_run import DOERun, DOEMeasurement
from app.utils.vpd_formula import vpd_kpa

# Optional: sklearn for importance
try:
    from sklearn.ensemble import RandomForestRegressor
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


def _factors_temp_rh(run: DOERun) -> tuple:
    factors = json.loads(run.factors_json) if run.factors_json else {}
    temp = factors.get("temp_c") or factors.get("temp") or 0.0
    rh = factors.get("rh_pct") or factors.get("rh") or 0.0
    return float(temp), float(rh)


def get_overlay_points(
    db: Session,
    metric_key: str,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    tool_id: Optional[str] = None,
    recipe_id: Optional[str] = None,
    batch_id: Optional[str] = None,
    outlier: bool = False,
) -> List[Dict[str, Any]]:
    """Return points for heatmap overlay: run_id, temp_c, rh_pct, vpd_kpa, metric_value, tool_id, recipe_id, batch_id, started_at."""
    q = db.query(DOERun, DOEMeasurement).join(
        DOEMeasurement, DOEMeasurement.run_id == DOERun.id
    ).filter(DOEMeasurement.metric_key == metric_key)
    if date_from:
        q = q.filter(DOERun.started_at >= date_from)
    if date_to:
        q = q.filter(DOERun.started_at <= date_to)
    if tool_id:
        q = q.filter(DOERun.tool_id == tool_id)
    if recipe_id:
        q = q.filter(DOERun.recipe_id == recipe_id)
    if batch_id:
        q = q.filter(DOERun.batch_id == batch_id)
    rows = q.all()
    out = []
    for run, meas in rows:
        temp_c, rh_pct = _factors_temp_rh(run)
        vpd = vpd_kpa(temp_c, rh_pct)
        out.append({
            "run_id": run.run_id,
            "temp_c": temp_c,
            "rh_pct": rh_pct,
            "vpd_kpa": round(vpd, 4),
            "metric_value": meas.metric_value,
            "tool_id": run.tool_id or "",
            "recipe_id": run.recipe_id or "",
            "batch_id": run.batch_id or "",
            "started_at": run.started_at.isoformat() if run.started_at else None,
        })
    return out


def get_run_detail(db: Session, run_id: str) -> Optional[Dict[str, Any]]:
    run = db.query(DOERun).filter(DOERun.run_id == run_id).first()
    if not run:
        return None
    measurements = db.query(DOEMeasurement).filter(DOEMeasurement.run_id == run.id).all()
    factors = json.loads(run.factors_json) if run.factors_json else {}
    return {
        "run_id": run.run_id,
        "tool_id": run.tool_id,
        "recipe_id": run.recipe_id,
        "batch_id": run.batch_id,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "ended_at": run.ended_at.isoformat() if run.ended_at else None,
        "factors": factors,
        "measurements": [{"metric_key": m.metric_key, "metric_value": m.metric_value, "unit": m.unit} for m in measurements],
        "notes": run.notes,
    }


def main_effects_data(
    db: Session,
    metric_key: str,
    factor_keys: Optional[List[str]] = None,
    n_bins: int = 3,
) -> List[Dict[str, Any]]:
    """Factor bins -> mean response. factor_keys default to temp_c, rh_pct."""
    runs = db.query(DOERun).all()
    if not runs:
        return []
    keys = factor_keys or ["temp_c", "rh_pct"]
    result = []
    for fk in keys:
        values = []
        responses = []
        for run in runs:
            factors = json.loads(run.factors_json) if run.factors_json else {}
            val = factors.get(fk)
            if val is None:
                continue
            meas = db.query(DOEMeasurement).filter(
                DOEMeasurement.run_id == run.id,
                DOEMeasurement.metric_key == metric_key,
            ).first()
            if not meas:
                continue
            values.append(float(val))
            responses.append(meas.metric_value)
        if not values:
            result.append({"factor": fk, "levels": [], "means": [], "counts": []})
            continue
        import numpy as np
        arr = np.array(values)
        resp_arr = np.array(responses)
        try:
            bins = np.percentile(arr, [100 * i / n_bins for i in range(n_bins + 1)])
            bins = np.unique(bins)
        except Exception:
            bins = np.linspace(arr.min(), arr.max(), n_bins + 1)
        means = []
        levels = []
        counts = []
        for i in range(len(bins) - 1):
            mask = (arr >= bins[i]) & (arr < bins[i + 1])
            if i == len(bins) - 2:
                mask = (arr >= bins[i]) & (arr <= bins[i + 1])
            if mask.sum() == 0:
                continue
            levels.append(round((bins[i] + bins[i + 1]) / 2, 2))
            means.append(float(np.mean(resp_arr[mask])))
            counts.append(int(mask.sum()))
        result.append({"factor": fk, "levels": levels, "means": means, "counts": counts})
    return result


def interaction_data(
    db: Session,
    metric_key: str,
    factor_a: str = "temp_c",
    factor_b: str = "rh_pct",
    n_bins: int = 3,
) -> Dict[str, Any]:
    """Matrix: factor_a bins x factor_b bins -> mean response."""
    runs = db.query(DOERun).all()
    if not runs:
        return {"factor_a": factor_a, "factor_b": factor_b, "matrix": [], "levels_a": [], "levels_b": []}
    import numpy as np
    va, vb, resp = [], [], []
    for run in runs:
        factors = json.loads(run.factors_json) if run.factors_json else {}
        a = factors.get(factor_a)
        b = factors.get(factor_b)
        if a is None or b is None:
            continue
        meas = db.query(DOEMeasurement).filter(
            DOEMeasurement.run_id == run.id,
            DOEMeasurement.metric_key == metric_key,
        ).first()
        if not meas:
            continue
        va.append(float(a))
        vb.append(float(b))
        resp.append(meas.metric_value)
    if not va:
        return {"factor_a": factor_a, "factor_b": factor_b, "matrix": [], "levels_a": [], "levels_b": []}
    va, vb, resp = np.array(va), np.array(vb), np.array(resp)
    try:
        edges_a = np.percentile(va, [100 * i / n_bins for i in range(n_bins + 1)])
        edges_b = np.percentile(vb, [100 * i / n_bins for i in range(n_bins + 1)])
    except Exception:
        edges_a = np.linspace(va.min(), va.max(), n_bins + 1)
        edges_b = np.linspace(vb.min(), vb.max(), n_bins + 1)
    levels_a = [round((edges_a[i] + edges_a[i + 1]) / 2, 2) for i in range(len(edges_a) - 1)]
    levels_b = [round((edges_b[i] + edges_b[i + 1]) / 2, 2) for i in range(len(edges_b) - 1)]
    matrix = []
    for i in range(len(edges_a) - 1):
        row = []
        for j in range(len(edges_b) - 1):
            ma = (va >= edges_a[i]) & (va < edges_a[i + 1])
            mb = (vb >= edges_b[j]) & (vb < edges_b[j + 1])
            if i == len(edges_a) - 2:
                ma = (va >= edges_a[i]) & (va <= edges_a[i + 1])
            if j == len(edges_b) - 2:
                mb = (vb >= edges_b[j]) & (vb <= edges_b[j + 1])
            m = ma & mb
            if m.sum() > 0:
                row.append(round(float(np.mean(resp[m])), 4))
            else:
                row.append(None)
        matrix.append(row)
    return {"factor_a": factor_a, "factor_b": factor_b, "matrix": matrix, "levels_a": levels_a, "levels_b": levels_b}


def importance_data(
    db: Session,
    metric_key: str,
    factor_keys: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Feature importance via RandomForest or fallback to abs(correlation)."""
    runs = db.query(DOERun).all()
    if not runs:
        return []
    keys = factor_keys or ["temp_c", "rh_pct"]
    X, y = [], []
    for run in runs:
        factors = json.loads(run.factors_json) if run.factors_json else {}
        row = [factors.get(k, 0.0) for k in keys]
        meas = db.query(DOEMeasurement).filter(
            DOEMeasurement.run_id == run.id,
            DOEMeasurement.metric_key == metric_key,
        ).first()
        if not meas:
            continue
        X.append(row)
        y.append(meas.metric_value)
    if len(X) < 3:
        return [{"factor": k, "importance": 0.0} for k in keys]
    import numpy as np
    X_arr = np.array(X, dtype=float)
    y_arr = np.array(y)
    if HAS_SKLEARN:
        try:
            model = RandomForestRegressor(n_estimators=20, random_state=42)
            model.fit(X_arr, y_arr)
            imp = model.feature_importances_
            return [{"factor": k, "importance": round(float(imp[i]), 4)} for i, k in enumerate(keys)]
        except Exception:
            pass
    # Fallback: abs correlation
    out = []
    for i, k in enumerate(keys):
        col = X_arr[:, i]
        if col.std() < 1e-9:
            out.append({"factor": k, "importance": 0.0})
            continue
        corr = np.corrcoef(col, y_arr)[0, 1]
        out.append({"factor": k, "importance": round(abs(corr) if not np.isnan(corr) else 0.0, 4)})
    return out
