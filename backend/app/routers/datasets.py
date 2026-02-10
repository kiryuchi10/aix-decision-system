from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Any
from pydantic import BaseModel, Field
import os
import uuid
import json
import pandas as pd
from datetime import datetime

from app.core.database import get_db
from app.models.user import User
from app.models.dataset import Dataset
from app.routers.auth import get_current_user
from dataclasses import asdict
from app.services.mat_reader import load_mat, build_inventory, inspect_mat

router = APIRouter(prefix="/datasets", tags=["Datasets"])

UPLOAD_DIR = "./app/data/uploads/datasets"
PREVIEW_DIR = "./app/data/reports/preview"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PREVIEW_DIR, exist_ok=True)
BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent


class DatasetResponse(BaseModel):
    id: int
    filename: str
    row_count: Optional[int]
    column_count: Optional[int]
    stage: Optional[str] = "DRAFT"
    committed: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class DatasetDetailResponse(DatasetResponse):
    storage_path: str
    schema_data: Optional[str] = Field(None, alias="schema_json", serialization_alias="schema_json")


class PreviewResponse(BaseModel):
    datasetId: int
    stage: str
    rowCount: int
    columnCount: int
    columns: List[Any]  # str or { name, type, description, missingCount }
    rows: Optional[List[dict]] = None
    wafersPreview: Optional[List[dict]] = None
    total_rows: Optional[int] = None


@router.post("/upload", response_model=DatasetResponse)
async def upload_dataset(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload CSV or .mat dataset (creates in DRAFT)."""
    fn = file.filename or "upload"
    if not (fn.endswith(".csv") or fn.endswith(".mat")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV and .mat files are allowed",
        )
    ext = ".csv" if fn.endswith(".csv") else ".mat"
    rid = uuid.uuid4().hex[:12]
    storage_path = os.path.join(UPLOAD_DIR, f"{rid}{ext}")
    with open(storage_path, "wb") as f:
        content = await file.read()
        f.write(content)

    row_count = None
    column_count = None
    schema_json_str = None
    try:
        if ext == ".csv":
            df = pd.read_csv(storage_path)
            row_count = len(df)
            column_count = len(df.columns)
            schema_json_str = json.dumps(df.dtypes.astype(str).to_dict())
        else:
            inv = inspect_mat(storage_path)
            info = inv.get("inventory", {})
            if info:
                n_calib = info.get("n_calib", 0)
                n_test = info.get("n_test", 0)
                row_count = n_calib + n_test
                column_count = info.get("variables_count", 0)
            schema_json_str = json.dumps(inv)
    except Exception as e:
        pass  # keep None meta

    dataset = Dataset(
        user_id=current_user.id,
        filename=file.filename,
        storage_path=storage_path,
        row_count=row_count,
        column_count=column_count,
        schema_json=schema_json_str,
        stage="DRAFT",
        committed=False,
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return dataset


@router.get("", response_model=List[DatasetResponse])
async def list_datasets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all datasets (include stage + committed)."""
    datasets = (
        db.query(Dataset)
        .filter(Dataset.user_id == current_user.id)
        .order_by(Dataset.created_at.desc())
        .all()
    )
    return datasets


@router.get("/{dataset_id}", response_model=DatasetDetailResponse)
async def get_dataset(
    dataset_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get dataset details (include columns/meta from inventory when available)."""
    dataset = (
        db.query(Dataset)
        .filter(Dataset.id == dataset_id, Dataset.user_id == current_user.id)
        .first()
    )
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dataset


def _preview_path(dataset_id: int) -> str:
    return os.path.join(PREVIEW_DIR, f"{dataset_id}.json")


@router.get("/{dataset_id}/preview")
async def get_preview(
    dataset_id: int,
    rows: int = Query(default=50, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get preview (from stored JSON if stage=PREVIEW, else build on the fly)."""
    dataset = (
        db.query(Dataset)
        .filter(Dataset.id == dataset_id, Dataset.user_id == current_user.id)
        .first()
    )
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    path = _preview_path(dataset_id)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    # Build on the fly
    return await _build_preview_response(dataset, rows, db)


@router.post("/{dataset_id}/preview")
async def post_preview(
    dataset_id: int,
    rows: int = Query(default=50, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Parse inventory + write preview summary JSON to disk, set stage=PREVIEW."""
    dataset = (
        db.query(Dataset)
        .filter(Dataset.id == dataset_id, Dataset.user_id == current_user.id)
        .first()
    )
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    payload = await _build_preview_response(dataset, rows, db)
    path = _preview_path(dataset_id)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    dataset.stage = "PREVIEW"
    db.commit()
    return payload


async def _build_preview_response(dataset: Dataset, rows: int, db: Session) -> dict:
    storage = dataset.storage_path
    if not os.path.isabs(storage):
        storage = os.path.join(BACKEND_ROOT, storage)
    if not os.path.exists(storage):
        raise HTTPException(status_code=404, detail="Dataset file not found")
    if storage.endswith(".mat"):
        mat = load_mat(storage)
        inv = build_inventory(mat, source_file=dataset.filename)
        wafers_preview = [asdict(w) for w in inv.wafers[:50]]
        columns = [{"name": v, "type": "numeric", "description": "", "missingCount": 0} for v in inv.variables]
        return {
            "datasetId": dataset.id,
            "stage": dataset.stage or "PREVIEW",
            "rowCount": inv.n_calib + inv.n_test,
            "columnCount": len(inv.variables),
            "columns": columns,
            "wafersPreview": wafers_preview,
            "total_rows": inv.n_calib + inv.n_test,
        }
    df = pd.read_csv(storage, nrows=rows)
    cols = df.columns.tolist()
    return {
        "datasetId": dataset.id,
        "stage": dataset.stage or "PREVIEW",
        "rowCount": dataset.row_count or len(df),
        "columnCount": len(cols),
        "columns": cols,
        "rows": df.head(rows).to_dict(orient="records"),
        "total_rows": dataset.row_count or len(df),
    }


@router.post("/{dataset_id}/undo-preview")
async def undo_preview(
    dataset_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete preview artifacts, set stage back to DRAFT."""
    dataset = (
        db.query(Dataset)
        .filter(Dataset.id == dataset_id, Dataset.user_id == current_user.id)
        .first()
    )
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    path = _preview_path(dataset_id)
    if os.path.exists(path):
        try:
            os.remove(path)
        except Exception:
            pass
    dataset.stage = "DRAFT"
    db.commit()
    return {"ok": True, "message": "Preview undone", "stage": "DRAFT"}


@router.post("/{dataset_id}/commit")
async def commit_dataset(
    dataset_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Set stage=COMMITTED and committed=True so pipeline can run."""
    dataset = (
        db.query(Dataset)
        .filter(Dataset.id == dataset_id, Dataset.user_id == current_user.id)
        .first()
    )
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    dataset.stage = "COMMITTED"
    dataset.committed = True
    db.commit()
    return {"ok": True, "message": "Dataset committed", "dataset_id": dataset_id, "stage": "COMMITTED"}
