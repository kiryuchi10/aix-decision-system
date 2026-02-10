# app/utils/vpd_formula.py
"""
VPD (Vapor Pressure Deficit) in kPa.
SVP(T) = saturation vapor pressure (Tetens), VPD = SVP(T) * (1 - RH/100).
"""

import math
from typing import List, Tuple


def svp_kpa(temp_c: float) -> float:
    """Saturation vapor pressure (kPa) at temperature T (°C). Tetens approximation."""
    if temp_c <= -50:
        return 0.0
    return 0.6108 * math.exp((17.27 * temp_c) / (temp_c + 237.3))


def vpd_kpa(temp_c: float, rh_pct: float) -> float:
    """VPD (kPa) = SVP(T) * (1 - RH/100)."""
    if rh_pct <= 0:
        return svp_kpa(temp_c)
    if rh_pct >= 100:
        return 0.0
    return svp_kpa(temp_c) * (1.0 - rh_pct / 100.0)


def build_vpd_grid(
    temp_min: float,
    temp_max: float,
    temp_step: float,
    rh_min: float,
    rh_max: float,
    rh_step: float,
) -> Tuple[List[float], List[float], List[List[float]]]:
    """
    Build 2D grid of VPD values.
    Returns (temps, rhs, matrix) where matrix[i][j] = VPD(temps[i], rhs[j]).
    """
    temps = []
    t = temp_min
    while t <= temp_max + 1e-9:
        temps.append(round(t, 2))
        t += temp_step
    rhs = []
    r = rh_min
    while r <= rh_max + 1e-9:
        rhs.append(round(r, 2))
        r += rh_step
    matrix = []
    for t in temps:
        row = []
        for r in rhs:
            row.append(round(vpd_kpa(t, r), 4))
        matrix.append(row)
    return temps, rhs, matrix


def sensitivity_vpd_dT(temp_c: float, rh_pct: float, delta_c: float = 1.0) -> float:
    """Approximate dVPD/dT (kPa/°C) at (temp_c, rh_pct)."""
    v0 = vpd_kpa(temp_c, rh_pct)
    v1 = vpd_kpa(temp_c + delta_c, rh_pct)
    return round((v1 - v0) / delta_c, 4)


def sensitivity_vpd_dRH(temp_c: float, rh_pct: float, delta_pct: float = 5.0) -> float:
    """Approximate dVPD/dRH (kPa per % RH). Negative: RH up -> VPD down."""
    v0 = vpd_kpa(temp_c, rh_pct)
    v1 = vpd_kpa(temp_c, rh_pct - delta_pct)  # RH down -> VPD up
    return round((v1 - v0) / (-delta_pct), 4)
