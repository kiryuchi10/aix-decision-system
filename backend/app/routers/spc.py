from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

from app.core.database import get_db
from app.models.spc import SPCMetric, SPCRuleViolation
from app.routers.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/spc", tags=["SPC Center"])

class ChartRequest(BaseModel):
    entity_type: str  # chamber, recipe, lot
    entity_id: str
    metric_name: str  # temperature, pressure, cd, etc.
    chart_type: str = "xbar_r"  # xbar_r, i_mr, ewma, cusum
    subgroup_size: int = 5
    data_range_hours: int = 24

class ChartResponse(BaseModel):
    chart_type: str
    mean: float
    std_dev: float
    ucl: float
    lcl: float
    cl: float
    cp: Optional[float] = None
    cpk: Optional[float] = None
    data_points: List[dict]
    violations: List[dict]

class ViolationResponse(BaseModel):
    id: int
    rule_number: int
    rule_name: str
    violation_type: str
    point_index: int
    point_value: float
    severity: str
    detected_at: datetime

@router.post("/chart", response_model=ChartResponse)
async def create_control_chart(
    request: ChartRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create SPC control chart"""
    # TODO: Fetch actual sensor data from database
    # For now, generate mock data
    np.random.seed(42)
    n_points = 100
    data = np.random.normal(850, 5, n_points)  # Mock temperature data
    
    # Calculate control limits
    mean = float(np.mean(data))
    std_dev = float(np.std(data))
    
    if request.chart_type == "xbar_r":
        # Xbar-R chart
        ucl = mean + 3 * std_dev
        lcl = mean - 3 * std_dev
        cl = mean
    else:
        # Default: I-MR chart
        ucl = mean + 3 * std_dev
        lcl = mean - 3 * std_dev
        cl = mean
    
    # Calculate capability indices (mock)
    spec_upper = 860
    spec_lower = 840
    cp = (spec_upper - spec_lower) / (6 * std_dev) if std_dev > 0 else None
    cpk = min(
        (spec_upper - mean) / (3 * std_dev),
        (mean - spec_lower) / (3 * std_dev)
    ) if std_dev > 0 else None
    
    # Detect rule violations (mock)
    violations = []
    for i, value in enumerate(data):
        if abs(value - mean) > 3 * std_dev:
            violations.append({
                "rule_number": 1,
                "rule_name": "Point beyond 3-sigma",
                "point_index": i,
                "point_value": float(value),
                "severity": "HIGH"
            })
    
    # Format data points
    data_points = [
        {"index": i, "value": float(v), "timestamp": (datetime.utcnow() - timedelta(hours=n_points-i)).isoformat()}
        for i, v in enumerate(data)
    ]
    
    return ChartResponse(
        chart_type=request.chart_type,
        mean=mean,
        std_dev=std_dev,
        ucl=ucl,
        lcl=lcl,
        cl=cl,
        cp=cp,
        cpk=cpk,
        data_points=data_points,
        violations=violations
    )

@router.get("/violations")
async def get_violations(
    range_hours: int = Query(24, ge=1, le=168),
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get SPC rule violations"""
    query = db.query(SPCRuleViolation)
    
    if entity_type and entity_id:
        # Filter by entity
        query = query.join(SPCMetric).filter(
            SPCMetric.entity_type == entity_type,
            SPCMetric.entity_id == entity_id
        )
    
    # Filter by time range
    cutoff_time = datetime.utcnow() - timedelta(hours=range_hours)
    query = query.filter(SPCRuleViolation.detected_at >= cutoff_time)
    
    violations = query.order_by(SPCRuleViolation.detected_at.desc()).limit(100).all()
    
    return [
        {
            "id": v.id,
            "rule_number": v.rule_number,
            "rule_name": v.rule_name,
            "violation_type": v.violation_type,
            "point_index": v.point_index,
            "point_value": v.point_value,
            "severity": v.severity,
            "status": v.status,
            "detected_at": v.detected_at.isoformat()
        }
        for v in violations
    ]

@router.get("/cpk-trend")
async def get_cpk_trend(
    entity: str = Query(..., description="chamber, recipe, or lot"),
    entity_id: Optional[str] = None,
    metric_name: Optional[str] = None,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get Cpk trend over time"""
    query = db.query(SPCMetric)
    
    if entity_id:
        query = query.filter(SPCMetric.entity_id == entity_id)
    
    if metric_name:
        query = query.filter(SPCMetric.metric_name == metric_name)
    
    # Filter by time range
    cutoff_time = datetime.utcnow() - timedelta(days=days)
    query = query.filter(SPCMetric.calculated_at >= cutoff_time)
    
    metrics = query.order_by(SPCMetric.calculated_at.asc()).all()
    
    return [
        {
            "timestamp": m.calculated_at.isoformat(),
            "cpk": m.cpk,
            "cp": m.cp,
            "mean": m.mean,
            "std_dev": m.std_dev,
            "entity_id": m.entity_id,
            "metric_name": m.metric_name
        }
        for m in metrics
    ]
