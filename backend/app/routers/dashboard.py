from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select

from ..core.database import get_db
from ..models.kpi import KPIHourly

router = APIRouter()

@router.get("/kpis/hourly")
def get_kpis_hourly(limit: int = 200, db: Session = Depends(get_db)):
    stmt = select(KPIHourly).order_by(KPIHourly.hour.desc()).limit(limit)
    rows = db.execute(stmt).scalars().all()
    # return newest->oldest; frontend can reverse if needed
    return [{
        "hour": r.hour.isoformat(),
        "overall_health": r.overall_health,
        "process_cpk": r.process_cpk,
        "drift_events": r.drift_events,
        "avg_recovery_min": r.avg_recovery_min,
        "yield_proxy_pct": r.yield_proxy_pct,
        "yield_gain_pct": r.yield_gain_pct,
        "exp_reduction_pct": r.exp_reduction_pct,
    } for r in rows]
