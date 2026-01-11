from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import random

router = APIRouter(prefix="/fdc", tags=["FDC Drift Sentinel"])

class SensorData(BaseModel):
    timestamp: datetime
    temperature: float
    pressure: float
    gas_flow: float
    power: float

class Alarm(BaseModel):
    id: str
    timestamp: datetime
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    type: str  # GRADUAL_DRIFT, STEP_CHANGE, INTERMITTENT
    parameter: str
    current_value: float
    threshold_value: float
    sigma_distance: float
    yield_impact: float
    status: str  # ACTIVE, ACKNOWLEDGED, RESOLVED

@router.get("/alarms/active")
async def get_active_alarms() -> List[Alarm]:
    """Get active alarms"""
    # Mock data for demo
    return [
        Alarm(
            id="ALM-001",
            timestamp=datetime.utcnow(),
            severity="HIGH",
            type="GRADUAL_DRIFT",
            parameter="Temperature",
            current_value=865.2,
            threshold_value=850.0,
            sigma_distance=2.3,
            yield_impact=-4.2,
            status="ACTIVE"
        ),
        Alarm(
            id="ALM-002",
            timestamp=datetime.utcnow(),
            severity="MEDIUM",
            type="STEP_CHANGE",
            parameter="Pressure",
            current_value=2.65,
            threshold_value=2.50,
            sigma_distance=1.8,
            yield_impact=-2.1,
            status="ACKNOWLEDGED"
        )
    ]

@router.get("/process-capability")
async def get_process_capability():
    """Get current process capability metrics"""
    return {
        "cpk": round(1.2 + random.uniform(-0.2, 0.2), 2),
        "cp": round(1.5 + random.uniform(-0.1, 0.1), 2),
        "drift_rate": round(0.05 + random.uniform(-0.02, 0.02), 3),
        "yield_estimate": round(92.5 + random.uniform(-2, 2), 1)
    }

@router.post("/sensor-data/ingest")
async def ingest_sensor_data(data: SensorData):
    """Ingest real-time sensor data"""
    # In production, this would store data and trigger drift detection
    return {"status": "success", "message": "Data ingested successfully"}