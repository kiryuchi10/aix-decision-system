from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime
import random
import uuid
import json
import csv
import io

from app.core.database import get_db
from app.routers.auth import get_current_user
from app.models.user import User
from app.models.doe_run import DOERun, DOEMeasurement
from app.services.doe_service import (
    get_overlay_points,
    get_run_detail,
    main_effects_data,
    interaction_data,
    importance_data,
)

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


# ---------- VPD DOE: overlay, runs, analysis ----------
@router.get("/overlay-points")
async def overlay_points(
    metric_key: str = Query(..., description="e.g. defect_rate, yield"),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    tool_id: Optional[str] = Query(None),
    recipe_id: Optional[str] = Query(None),
    batch_id: Optional[str] = Query(None),
    outlier: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lightweight points for heatmap overlay (run_id, temp_c, rh_pct, vpd_kpa, metric_value, ...)."""
    points = get_overlay_points(
        db, metric_key,
        date_from=date_from, date_to=date_to,
        tool_id=tool_id, recipe_id=recipe_id, batch_id=batch_id,
        outlier=outlier,
    )
    return {"metric_key": metric_key, "points": points}


@router.get("/runs")
async def list_doe_runs(
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    tool_id: Optional[str] = Query(None),
    recipe_id: Optional[str] = Query(None),
    batch_id: Optional[str] = Query(None),
    metric_key: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List DOE runs with optional filters."""
    q = db.query(DOERun)
    if date_from:
        q = q.filter(DOERun.started_at >= date_from)
    if date_to:
        q = q.filter(DOERun.started_at <= date_to)
    if tool_id:
        q = q.filter(DOERun.tool_id == tool_id)
    if recipe_id:
        q = q.filter(DOERun.recipe_id == recipe_id)
    if batch_id:
        q = q.filter(DOERun.batch_id == batch_id)
    runs = q.order_by(DOERun.created_at.desc()).limit(200).all()
    out = []
    for r in runs:
        measurements = db.query(DOEMeasurement).filter(DOEMeasurement.run_id == r.id).all()
        if metric_key and not any(m.metric_key == metric_key for m in measurements):
            continue
        out.append({
            "run_id": r.run_id,
            "tool_id": r.tool_id,
            "recipe_id": r.recipe_id,
            "batch_id": r.batch_id,
            "started_at": r.started_at.isoformat() if r.started_at else None,
            "factors": json.loads(r.factors_json) if r.factors_json else {},
            "measurements": [{"metric_key": m.metric_key, "metric_value": m.metric_value} for m in measurements],
        })
    return {"runs": out}


@router.get("/runs/{run_id}")
async def get_doe_run(
    run_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get single run detail for drawer."""
    detail = get_run_detail(db, run_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Run not found")
    return detail


@router.post("/runs/import")
async def import_doe_runs(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Import DOE runs from CSV. Columns: run_id, tool_id, recipe_id, batch_id, started_at, temp_c, rh_pct, [metric_key columns]."""
    content = await file.read()
    try:
        text = content.decode("utf-8")
    except Exception:
        text = content.decode("latin-1")
    reader = csv.DictReader(io.StringIO(text))
    rows = list(reader)
    if not rows:
        return {"imported": 0, "message": "No rows"}
    imported = 0
    for row in rows:
        run_id = (row.get("run_id") or row.get("id") or "").strip()
        if not run_id:
            continue
        if db.query(DOERun).filter(DOERun.run_id == run_id).first():
            continue
        try:
            started = None
            if row.get("started_at"):
                from dateutil import parser as date_parser
                started = date_parser.parse(row["started_at"])
        except Exception:
            pass
        factors = {"temp_c": float(row.get("temp_c", 0)), "rh_pct": float(row.get("rh_pct", 0))}
        run = DOERun(
            run_id=run_id,
            tool_id=row.get("tool_id"),
            recipe_id=row.get("recipe_id"),
            batch_id=row.get("batch_id"),
            started_at=started,
            factors_json=json.dumps(factors),
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        for k, v in row.items():
            if k in ("run_id", "tool_id", "recipe_id", "batch_id", "started_at", "temp_c", "rh_pct", "notes"):
                continue
            try:
                val = float(v)
            except (ValueError, TypeError):
                continue
            m = DOEMeasurement(run_id=run.id, metric_key=k, metric_value=val)
            db.add(m)
        db.commit()
        imported += 1
    return {"imported": imported, "total_rows": len(rows)}


@router.get("/runs")
async def list_doe_runs(
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    tool_id: Optional[str] = Query(None),
    recipe_id: Optional[str] = Query(None),
    batch_id: Optional[str] = Query(None),
    metric_key: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List DOE runs with optional filters."""
    q = db.query(DOERun)
    if date_from:
        q = q.filter(DOERun.started_at >= date_from)
    if date_to:
        q = q.filter(DOERun.started_at <= date_to)
    if tool_id:
        q = q.filter(DOERun.tool_id == tool_id)
    if recipe_id:
        q = q.filter(DOERun.recipe_id == recipe_id)
    if batch_id:
        q = q.filter(DOERun.batch_id == batch_id)
    runs = q.order_by(DOERun.created_at.desc()).limit(200).all()
    out = []
    for r in runs:
        measurements = db.query(DOEMeasurement).filter(DOEMeasurement.run_id == r.id).all()
        if metric_key and not any(m.metric_key == metric_key for m in measurements):
            continue
        out.append({
            "run_id": r.run_id,
            "tool_id": r.tool_id,
            "recipe_id": r.recipe_id,
            "batch_id": r.batch_id,
            "started_at": r.started_at.isoformat() if r.started_at else None,
            "factors": json.loads(r.factors_json) if r.factors_json else {},
            "measurements": [{"metric_key": m.metric_key, "metric_value": m.metric_value} for m in measurements],
        })
    return {"runs": out}


@router.get("/runs/{run_id}")
async def get_doe_run(
    run_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get single run detail for drawer."""
    detail = get_run_detail(db, run_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Run not found")
    return detail


@router.get("/analysis/main-effects")
async def analysis_main_effects(
    metric_key: str = Query(...),
    factor_keys: Optional[str] = Query(None),  # comma-separated
    n_bins: int = Query(3, ge=2, le=10),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Main effects: factor bins -> mean response."""
    keys = [x.strip() for x in factor_keys.split(",")] if factor_keys else None
    data = main_effects_data(db, metric_key, factor_keys=keys, n_bins=n_bins)
    return {"metric_key": metric_key, "effects": data}


@router.get("/analysis/interaction")
async def analysis_interaction(
    metric_key: str = Query(...),
    factor_a: str = Query("temp_c"),
    factor_b: str = Query("rh_pct"),
    n_bins: int = Query(3, ge=2, le=10),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Interaction: factor_a x factor_b -> mean response matrix."""
    data = interaction_data(db, metric_key, factor_a=factor_a, factor_b=factor_b, n_bins=n_bins)
    return data


@router.get("/analysis/importance")
async def analysis_importance(
    metric_key: str = Query(...),
    factor_keys: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Factor importance (RF or correlation)."""
    keys = [x.strip() for x in factor_keys.split(",")] if factor_keys else None
    data = importance_data(db, metric_key, factor_keys=keys)
    return {"metric_key": metric_key, "importance": data}