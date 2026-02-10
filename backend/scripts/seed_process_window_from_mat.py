#!/usr/bin/env python3
"""Seed VPD/Process Window from real .mat wafer features (MACHINE_Data.mat)."""
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from app.core.database import SessionLocal
from app.models.vpd import VPDGrid, VPDSetting
from app.models.doe_run import DOERun, DOEMeasurement
from app.services.vpd_service import create_grid
from app.services.mat_reader import mat_to_wafer_feature_df

BACKEND_ROOT = Path(__file__).resolve().parent.parent
MAT_PATH = BACKEND_ROOT / "app" / "data" / "seed" / "process_etch" / "MACHINE_Data.mat"


def main():
    db = SessionLocal()
    try:
        if not MAT_PATH.exists():
            raise FileNotFoundError(str(MAT_PATH))

        df = mat_to_wafer_feature_df(MAT_PATH, limit=5000)

        existing = db.query(VPDGrid).first()
        if not existing:
            feat_cols = [c for c in df.columns if c.endswith("__mean")]
            xcol = feat_cols[0]
            ycol = feat_cols[1] if len(feat_cols) > 1 else feat_cols[0]
            x = df[xcol].replace([np.inf, -np.inf], np.nan).dropna()
            y = df[ycol].replace([np.inf, -np.inf], np.nan).dropna()
            x_min, x_max = float(x.quantile(0.05)), float(x.quantile(0.95))
            y_min, y_max = float(y.quantile(0.05)), float(y.quantile(0.95))
            grid = create_grid(
                x_min, x_max, (x_max - x_min) / 20.0,
                y_min, y_max, (y_max - y_min) / 20.0,
                db,
            )
            print(f"Created grid: {grid.grid_id} ({xcol} vs {ycol})")
        else:
            grid = existing
            print(f"Using existing grid: {grid.grid_id}")

        if db.query(VPDSetting).first() is None:
            s = VPDSetting(
                name="Etch-ProcessWindow(Default)",
                target_min_kpa=0.0,
                target_max_kpa=0.0,
                temp_constraint_min=0.0,
                temp_constraint_max=0.0,
                rh_constraint_min=0.0,
                rh_constraint_max=0.0,
                metric_key="fault_score",
                recommend_mode="simple",
            )
            db.add(s)
            db.commit()
            print("Created setting: Etch-ProcessWindow(Default)")

        feat_cols = [c for c in df.columns if c.endswith("__mean")]
        xcol = feat_cols[0]
        ycol = feat_cols[1] if len(feat_cols) > 1 else feat_cols[0]
        base = datetime.utcnow() - timedelta(days=7)
        sample = df.sample(n=min(20, len(df)), random_state=42).reset_index(drop=True)

        for i in range(len(sample)):
            run_id = f"R-REAL-{i + 1:03d}"
            if db.query(DOERun).filter(DOERun.run_id == run_id).first():
                continue
            xv = float(sample.loc[i, xcol])
            yv = float(sample.loc[i, ycol])
            label = int(sample.loc[i, "label"])

            run = DOERun(
                run_id=run_id,
                tool_id="ETCH_T01",
                recipe_id="REC-REAL",
                batch_id=f"B{i // 5 + 1}",
                started_at=base + timedelta(hours=i * 3),
                factors_json=json.dumps({"x_factor": xcol, "y_factor": ycol, "x": xv, "y": yv}),
            )
            db.add(run)
            db.commit()
            db.refresh(run)

            fault_score = 1.0 if label == 1 else 0.0
            yield_pct = 92.0 + (0.5 - fault_score) * 6.0

            db.add(DOEMeasurement(run_id=run.id, metric_key="fault_score", metric_value=fault_score, unit="score"))
            db.add(DOEMeasurement(run_id=run.id, metric_key="yield", metric_value=float(yield_pct), unit="%"))
            db.commit()

        print("Seeded 20 REAL DOE runs from MACHINE_Data.mat features")
    finally:
        db.close()


if __name__ == "__main__":
    main()
