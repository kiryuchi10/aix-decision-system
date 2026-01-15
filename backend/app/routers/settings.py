"""
Settings Router
- Process Window (guardrails)
- Alarm Thresholds
- System Configuration
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.routers.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/settings", tags=["Settings"])


# Process Window Models
class ProcessWindowRow(BaseModel):
    key: str
    unit: Optional[str] = None
    hardMin: float
    hardMax: float
    note: Optional[str] = None


class ProcessWindowResponse(BaseModel):
    updatedAt: Optional[str] = None
    rows: List[ProcessWindowRow]


# Alarm Thresholds Models
class AlarmThresholds(BaseModel):
    enableWeco: bool = True
    sigmaThreshold: float = 3.0
    ewmaLambda: float = 0.2


# Default process window (can be stored in DB later)
DEFAULT_PROCESS_WINDOW = ProcessWindowResponse(
    updatedAt=datetime.utcnow().isoformat(),
    rows=[
        ProcessWindowRow(key="pressure_torr", unit="Torr", hardMin=20.0, hardMax=60.0, note="Chamber pressure window"),
        ProcessWindowRow(key="bias_power_w", unit="W", hardMin=0.0, hardMax=500.0, note="RF bias power safety range"),
        ProcessWindowRow(key="chuck_temp_c", unit="°C", hardMin=10.0, hardMax=80.0),
        ProcessWindowRow(key="temperature", unit="°C", hardMin=840.0, hardMax=860.0, note="Process temperature range"),
    ]
)

DEFAULT_ALARM_THRESHOLDS = AlarmThresholds(
    enableWeco=True,
    sigmaThreshold=3.0,
    ewmaLambda=0.2
)


@router.get("/process-window", response_model=ProcessWindowResponse)
async def get_process_window(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get process window guardrails"""
    # TODO: Load from database
    # For now, return default
    return DEFAULT_PROCESS_WINDOW


@router.post("/process-window", response_model=dict)
async def save_process_window(
    payload: ProcessWindowResponse,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Save process window guardrails"""
    # TODO: Save to database
    # For now, just validate and return success
    if not payload.rows:
        raise HTTPException(status_code=400, detail="Process window rows cannot be empty")
    
    # Validate ranges
    for row in payload.rows:
        if row.hardMin >= row.hardMax:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid range for {row.key}: min must be less than max"
            )
    
    return {"ok": True, "message": "Process window saved successfully"}


@router.get("/alarm-thresholds", response_model=AlarmThresholds)
async def get_alarm_thresholds(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get alarm thresholds"""
    # TODO: Load from database
    return DEFAULT_ALARM_THRESHOLDS


@router.post("/alarm-thresholds", response_model=dict)
async def save_alarm_thresholds(
    payload: AlarmThresholds,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Save alarm thresholds"""
    # TODO: Save to database
    if payload.sigmaThreshold < 0:
        raise HTTPException(status_code=400, detail="Sigma threshold must be positive")
    if not (0 < payload.ewmaLambda < 1):
        raise HTTPException(status_code=400, detail="EWMA lambda must be between 0 and 1")
    
    return {"ok": True, "message": "Alarm thresholds saved successfully"}
