from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime
import random
import uuid
import json

from app.core.database import get_db
from app.routers.auth import get_current_user
from app.models.user import User

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

class SavePlanRequest(BaseModel):
    project_id: Optional[str] = None
    method: str  # pb, frac_fact, full_fact, ccd, bb, lhs, bayes
    factor_spec: List[Dict]
    design_matrix: List[Dict]
    name: Optional[str] = None

class SavePlanResponse(BaseModel):
    plan_id: str
    message: str

@router.post("/plans", response_model=SavePlanResponse)
async def save_plan(
    request: SavePlanRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Save DoE plan"""
    plan_id = f"PLAN-{uuid.uuid4().hex[:8].upper()}"
    
    # TODO: Save to database (doe_plans table)
    # For now, return success
    return SavePlanResponse(
        plan_id=plan_id,
        message=f"Plan saved successfully. ID: {plan_id}"
    )

class SubmitResultsRequest(BaseModel):
    plan_id: str
    results: List[Dict]  # [{run: 1, y: {Yield: 95.2, ...}, status: "DONE"}, ...]

@router.post("/plans/{plan_id}/results")
async def submit_results(
    plan_id: str,
    request: SubmitResultsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit experiment results"""
    # TODO: Save results to database
    return {
        "status": "success",
        "message": f"Results submitted for plan {plan_id}",
        "results_count": len(request.results)
    }

class AnalyzeRequest(BaseModel):
    plan_id: str
    response: str  # response metric name (e.g., "Yield")

class AnalyzeResponse(BaseModel):
    main_effects: List[Dict]
    anova: Dict
    r2: Optional[float] = None
    adj_r2: Optional[float] = None
    rmse: Optional[float] = None
    suggested_next: Optional[Dict] = None

@router.post("/plans/{plan_id}/analyze", response_model=AnalyzeResponse)
async def analyze_plan(
    plan_id: str,
    request: AnalyzeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Run statistical analysis on experiment results"""
    # TODO: Implement actual analysis (ANOVA, main effects, etc.)
    # Mock response for now
    return AnalyzeResponse(
        main_effects=[
            {"factor": "Temperature", "effect": 2.3, "p": 0.001},
            {"factor": "Pressure", "effect": 1.8, "p": 0.005},
            {"factor": "Gas Flow", "effect": 0.9, "p": 0.02},
        ],
        anova={
            "model": {"df": 3, "ss": 45.2, "ms": 15.07, "f": 12.5, "p": 0.001},
            "residual": {"df": 20, "ss": 24.1, "ms": 1.21},
            "total": {"df": 23, "ss": 69.3}
        },
        r2=0.65,
        adj_r2=0.60,
        rmse=1.10,
        suggested_next={
            "next_experiment": {"temperature": 847.5, "pressure": 2.45},
            "expected_improvement": 2.3
        }
    )

class RecommendNextRequest(BaseModel):
    plan_id: str
    response: str
    n: int = 3

@router.post("/plans/{plan_id}/recommend-next")
async def recommend_next(
    plan_id: str,
    request: RecommendNextRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Recommend next best experiments"""
    # TODO: Implement Bayesian optimization or other recommendation algorithm
    # Mock response
    recommendations = []
    for i in range(request.n):
        recommendations.append({
            "rank": i + 1,
            "parameters": {
                "temperature": 847.5 + i * 2.5,
                "pressure": 2.45 + i * 0.05
            },
            "information_gain": 0.92 - i * 0.04,
            "expected_improvement": 2.3 - i * 0.3,
            "confidence": 0.87 - i * 0.03
        })
    
    return {
        "acq": "EI",  # Expected Improvement
        "points": recommendations
    }

@router.get("/plans/{plan_id}")
async def get_plan(
    plan_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get plan details"""
    # TODO: Fetch from database
    return {
        "plan_id": plan_id,
        "method": "ccd",
        "factor_spec": [
            {"name": "Temp", "type": "continuous", "low": 180, "high": 220, "unit": "°C"},
            {"name": "Pressure", "type": "continuous", "low": 10, "high": 30, "unit": "mTorr"},
        ],
        "design_matrix": [],
        "run_results": [],
        "analysis": None,
        "recommendations": None
    }

@router.get("/plans")
async def list_plans(
    project_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all plans"""
    # TODO: Fetch from database
    return {
        "plans": [
            {
                "id": "PLAN-001",
                "name": "CCD Optimization",
                "method": "ccd",
                "created_at": datetime.utcnow().isoformat()
            }
        ]
    }

@router.get("/plans/{plan_id}/plots")
async def get_plots(
    plan_id: str,
    plot_type: Optional[str] = None,  # main_effects, interaction, contour, surface, residuals
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get plot data for visualization"""
    # TODO: Generate actual plot data
    # Mock response
    return {
        "plot_type": plot_type or "main_effects",
        "data": {
            "x": [180, 190, 200, 210, 220],
            "y": [95.2, 96.1, 97.5, 96.8, 95.9],
            "factors": ["Temp", "Pressure"]
        },
        "config": {
            "title": "Main Effects Plot",
            "x_label": "Factor Level",
            "y_label": "Response"
        }
    }