from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime
import random

router = APIRouter(prefix="/doe", tags=["DoE Planner"])

class Experiment(BaseModel):
    id: str
    parameters: Dict[str, float]
    objectives: List[str]
    status: str  # PLANNED, RUNNING, COMPLETED
    information_gain: Optional[float] = None
    estimated_duration: Optional[int] = None  # minutes

class ProcessWindow(BaseModel):
    parameter: str
    min_value: float
    max_value: float
    optimal_value: float
    current_value: float

@router.get("/experiments/active")
async def get_active_experiments() -> List[Experiment]:
    """Get active experiments"""
    return [
        Experiment(
            id="EXP-001",
            parameters={"temperature": 845.0, "pressure": 2.4},
            objectives=["maximize_yield", "minimize_defects"],
            status="RUNNING",
            information_gain=0.85,
            estimated_duration=120
        ),
        Experiment(
            id="EXP-002",
            parameters={"temperature": 855.0, "pressure": 2.6},
            objectives=["maximize_yield"],
            status="PLANNED",
            information_gain=0.72,
            estimated_duration=90
        )
    ]

@router.get("/process-window")
async def get_process_window() -> List[ProcessWindow]:
    """Get current process window status"""
    return [
        ProcessWindow(
            parameter="Temperature",
            min_value=840.0,
            max_value=860.0,
            optimal_value=850.0,
            current_value=852.3
        ),
        ProcessWindow(
            parameter="Pressure",
            min_value=2.3,
            max_value=2.7,
            optimal_value=2.5,
            current_value=2.48
        )
    ]

@router.get("/recommendations/next")
async def get_next_experiment_recommendations():
    """Get next recommended experiments"""
    return {
        "recommendations": [
            {
                "rank": 1,
                "parameters": {"temperature": 847.5, "pressure": 2.45},
                "information_gain": 0.92,
                "expected_improvement": 2.3,
                "confidence": 0.87
            },
            {
                "rank": 2,
                "parameters": {"temperature": 852.0, "pressure": 2.55},
                "information_gain": 0.88,
                "expected_improvement": 1.9,
                "confidence": 0.82
            },
            {
                "rank": 3,
                "parameters": {"temperature": 849.0, "pressure": 2.52},
                "information_gain": 0.84,
                "expected_improvement": 1.7,
                "confidence": 0.79
            }
        ]
    }

@router.get("/status")
async def get_doe_status():
    """Get DoE system status"""
    return {
        "active_experiments": 2,
        "completed_experiments": 15,
        "pending_experiments": 3,
        "model_accuracy": round(89.5 + random.uniform(-2, 2), 1)
    }