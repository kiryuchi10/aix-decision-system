# app/services/vpd_service.py
import json
import uuid
from typing import List, Optional, Dict, Any

from app.utils.vpd_formula import (
    build_vpd_grid,
    vpd_kpa,
    sensitivity_vpd_dT,
    sensitivity_vpd_dRH,
)
from app.models.vpd import VPDGrid, VPDSetting


def create_grid(
    temp_min: float,
    temp_max: float,
    temp_step: float,
    rh_min: float,
    rh_max: float,
    rh_step: float,
    db,
) -> VPDGrid:
    temps, rhs, matrix = build_vpd_grid(
        temp_min, temp_max, temp_step, rh_min, rh_max, rh_step
    )
    grid_id = f"grid-{uuid.uuid4().hex[:12]}"
    grid = VPDGrid(
        grid_id=grid_id,
        temp_min=temp_min,
        temp_max=temp_max,
        temp_step=temp_step,
        rh_min=rh_min,
        rh_max=rh_max,
        rh_step=rh_step,
        temps_json=json.dumps(temps),
        rhs_json=json.dumps(rhs),
        vpd_matrix_json=json.dumps(matrix),
    )
    db.add(grid)
    db.commit()
    db.refresh(grid)
    return grid


def get_grid_by_id(grid_id: str, db) -> Optional[VPDGrid]:
    return db.query(VPDGrid).filter(VPDGrid.grid_id == grid_id).first()


def recommend_setpoint_simple(
    setting: VPDSetting,
    grid: VPDGrid,
) -> Dict[str, Any]:
    """
    From grid, filter by constraints and target band; choose point with max margin
    (min distance to band boundary).
    """
    import json as _json
    temps = _json.loads(grid.temps_json)
    rhs = _json.loads(grid.rhs_json)
    matrix = _json.loads(grid.vpd_matrix_json)
    t_min = setting.temp_constraint_min if setting.temp_constraint_min is not None else grid.temp_min
    t_max = setting.temp_constraint_max if setting.temp_constraint_max is not None else grid.temp_max
    r_min = setting.rh_constraint_min if setting.rh_constraint_min is not None else grid.rh_min
    r_max = setting.rh_constraint_max if setting.rh_constraint_max is not None else grid.rh_max
    low, high = setting.target_min_kpa, setting.target_max_kpa

    best = None
    best_margin = -1.0
    for i, t in enumerate(temps):
        if t < t_min or t > t_max:
            continue
        for j, r in enumerate(rhs):
            if r < r_min or r > r_max:
                continue
            vpd = matrix[i][j]
            if vpd < low or vpd > high:
                continue
            margin = min(vpd - low, high - vpd)
            if margin > best_margin:
                best_margin = margin
                best = (t, r, vpd)

    if best is None:
        return {
            "temp_c": None,
            "rh_pct": None,
            "vpd_kpa": None,
            "margin": None,
            "sensitivity": {"dVPD_dT": None, "dVPD_dRH": None},
            "message": "No point in target band within constraints",
        }
    temp_c, rh_pct, vpd_kpa_val = best
    return {
        "temp_c": temp_c,
        "rh_pct": rh_pct,
        "vpd_kpa": vpd_kpa_val,
        "margin": round(best_margin, 4),
        "sensitivity": {
            "dVPD_dT": sensitivity_vpd_dT(temp_c, rh_pct),
            "dVPD_dRH": sensitivity_vpd_dRH(temp_c, rh_pct),
        },
        "message": "OK",
    }
