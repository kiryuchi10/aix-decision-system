# app/routers/vpd.py
"""VPD Process Window: grids, settings, recommend setpoint."""
import json
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.routers.auth import get_current_user
from app.models.user import User
from app.models.vpd import VPDGrid, VPDSetting
from app.services.vpd_service import create_grid, get_grid_by_id, recommend_setpoint_simple

router = APIRouter(prefix="/vpd", tags=["VPD Process Window"])


# ----- Schemas -----
class GridCreateRequest(BaseModel):
    temp_min: float
    temp_max: float
    temp_step: float
    rh_min: float
    rh_max: float
    rh_step: float


class GridResponse(BaseModel):
    grid_id: str
    temps: List[float]
    rhs: List[float]
    matrix: List[List[float]]

    class Config:
        from_attributes = True


class SettingResponse(BaseModel):
    id: int
    name: str
    target_min_kpa: float
    target_max_kpa: float
    temp_constraint_min: Optional[float]
    temp_constraint_max: Optional[float]
    rh_constraint_min: Optional[float]
    rh_constraint_max: Optional[float]
    metric_key: str
    recommend_mode: str
    created_at: datetime

    class Config:
        from_attributes = True


class SettingCreate(BaseModel):
    name: str
    target_min_kpa: float
    target_max_kpa: float
    temp_constraint_min: Optional[float] = None
    temp_constraint_max: Optional[float] = None
    rh_constraint_min: Optional[float] = None
    rh_constraint_max: Optional[float] = None
    metric_key: str = "defect_rate"
    recommend_mode: str = "simple"


class RecommendRequest(BaseModel):
    setting_id: int
    grid_id: str


class RecommendResponse(BaseModel):
    temp_c: Optional[float]
    rh_pct: Optional[float]
    vpd_kpa: Optional[float]
    margin: Optional[float]
    sensitivity: dict
    message: str


# ----- Routes -----
@router.post("/grids", response_model=dict)
async def post_grid(
    body: GridCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create VPD grid. Returns { grid_id }."""
    grid = create_grid(
        body.temp_min, body.temp_max, body.temp_step,
        body.rh_min, body.rh_max, body.rh_step,
        db,
    )
    return {"grid_id": grid.grid_id}


@router.get("/grids/{grid_id}", response_model=GridResponse)
async def get_grid(
    grid_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get grid by id. Returns temps, rhs, matrix."""
    grid = get_grid_by_id(grid_id, db)
    if not grid:
        raise HTTPException(status_code=404, detail="Grid not found")
    return GridResponse(
        grid_id=grid.grid_id,
        temps=json.loads(grid.temps_json),
        rhs=json.loads(grid.rhs_json),
        matrix=json.loads(grid.vpd_matrix_json),
    )


@router.get("/settings", response_model=List[SettingResponse])
async def list_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List VPD settings."""
    rows = db.query(VPDSetting).order_by(VPDSetting.updated_at.desc()).all()
    return rows


@router.post("/settings", response_model=SettingResponse)
async def create_setting(
    body: SettingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create VPD setting."""
    s = VPDSetting(
        name=body.name,
        target_min_kpa=body.target_min_kpa,
        target_max_kpa=body.target_max_kpa,
        temp_constraint_min=body.temp_constraint_min,
        temp_constraint_max=body.temp_constraint_max,
        rh_constraint_min=body.rh_constraint_min,
        rh_constraint_max=body.rh_constraint_max,
        metric_key=body.metric_key,
        recommend_mode=body.recommend_mode,
        created_by_user_id=current_user.id,
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


@router.put("/settings/{setting_id}", response_model=SettingResponse)
async def update_setting(
    setting_id: int,
    body: SettingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update VPD setting."""
    s = db.query(VPDSetting).filter(VPDSetting.id == setting_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Setting not found")
    s.name = body.name
    s.target_min_kpa = body.target_min_kpa
    s.target_max_kpa = body.target_max_kpa
    s.temp_constraint_min = body.temp_constraint_min
    s.temp_constraint_max = body.temp_constraint_max
    s.rh_constraint_min = body.rh_constraint_min
    s.rh_constraint_max = body.rh_constraint_max
    s.metric_key = body.metric_key
    s.recommend_mode = body.recommend_mode
    s.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(s)
    return s


@router.post("/recommend", response_model=RecommendResponse)
async def recommend(
    body: RecommendRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get recommended setpoint (simple: max margin in target band)."""
    setting = db.query(VPDSetting).filter(VPDSetting.id == body.setting_id).first()
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    grid = get_grid_by_id(body.grid_id, db)
    if not grid:
        raise HTTPException(status_code=404, detail="Grid not found")
    result = recommend_setpoint_simple(setting, grid)
    return RecommendResponse(**result)
