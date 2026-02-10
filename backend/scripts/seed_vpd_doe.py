#!/usr/bin/env python3
"""Seed VPD grid, one setting, and sample DOE runs for Process Window dashboard."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime, timedelta
import json
from app.core.database import SessionLocal
from app.models.vpd import VPDGrid, VPDSetting
from app.models.doe_run import DOERun, DOEMeasurement
from app.services.vpd_service import create_grid


def main():
    db = SessionLocal()
    try:
        # Default grid if none
        existing = db.query(VPDGrid).first()
        if not existing:
            grid = create_grid(20.0, 30.0, 1.0, 40.0, 80.0, 2.0, db)
            print(f"Created VPD grid: {grid.grid_id}")
        else:
            grid = existing
            print(f"Using existing grid: {grid.grid_id}")

        # One setting
        if db.query(VPDSetting).first() is None:
            s = VPDSetting(
                name="Default",
                target_min_kpa=0.8,
                target_max_kpa=1.2,
                temp_constraint_min=22.0,
                temp_constraint_max=28.0,
                rh_constraint_min=50.0,
                rh_constraint_max=70.0,
                metric_key="defect_rate",
                recommend_mode="simple",
            )
            db.add(s)
            db.commit()
            print("Created VPD setting: Default")

        # Sample DOE runs (20)
        base = datetime.utcnow() - timedelta(days=7)
        for i in range(20):
            run_id = f"R-2026-{i+1:03d}"
            if db.query(DOERun).filter(DOERun.run_id == run_id).first():
                continue
            temp = 22.0 + (i % 7)
            rh = 52.0 + (i % 5) * 4
            run = DOERun(
                run_id=run_id,
                tool_id="T01",
                recipe_id="REC-A",
                batch_id=f"B{i//5 + 1}",
                started_at=base + timedelta(hours=i*3),
                factors_json=json.dumps({"temp_c": temp, "rh_pct": rh}),
            )
            db.add(run)
            db.commit()
            db.refresh(run)
            # defect_rate and yield
            db.add(DOEMeasurement(run_id=run.id, metric_key="defect_rate", metric_value=1.5 + (i % 10) * 0.3, unit="%"))
            db.add(DOEMeasurement(run_id=run.id, metric_key="yield", metric_value=94.0 + (i % 6), unit="%"))
            db.commit()
        print("Seeded 20 DOE runs with defect_rate and yield")
    finally:
        db.close()


if __name__ == "__main__":
    main()
