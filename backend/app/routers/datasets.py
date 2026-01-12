from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import os
import uuid
import pandas as pd
from datetime import datetime

from app.core.database import get_db
from app.models.user import User
from app.models.dataset import Dataset
from app.routers.auth import get_current_user

router = APIRouter(prefix="/datasets", tags=["Datasets"])

UPLOAD_DIR = "./app/data/uploads/datasets"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class DatasetResponse(BaseModel):
    id: int
    filename: str
    row_count: Optional[int]
    column_count: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True

class DatasetDetailResponse(DatasetResponse):
    storage_path: str
    schema_json: Optional[str]

class PreviewResponse(BaseModel):
    columns: List[str]
    rows: List[dict]
    total_rows: int

@router.post("/upload", response_model=DatasetResponse)
async def upload_dataset(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a CSV dataset"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are allowed"
        )
    
    # Generate unique filename
    dataset_id = uuid.uuid4().hex[:12]
    filename = f"{dataset_id}.csv"
    storage_path = os.path.join(UPLOAD_DIR, filename)
    
    # Save file
    with open(storage_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # Read CSV to get metadata
    try:
        df = pd.read_csv(storage_path)
        row_count = len(df)
        column_count = len(df.columns)
        schema_json = df.dtypes.to_dict()
        schema_json_str = str(schema_json)
    except Exception as e:
        row_count = None
        column_count = None
        schema_json_str = None
    
    # Create database record
    dataset = Dataset(
        user_id=current_user.id,
        filename=file.filename,
        storage_path=storage_path,
        row_count=row_count,
        column_count=column_count,
        schema_json=schema_json_str
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    
    return dataset

@router.get("", response_model=List[DatasetResponse])
async def list_datasets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all datasets for current user"""
    datasets = db.query(Dataset).filter(Dataset.user_id == current_user.id).order_by(Dataset.created_at.desc()).all()
    return datasets

@router.get("/{dataset_id}", response_model=DatasetDetailResponse)
async def get_dataset(
    dataset_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get dataset details"""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id, Dataset.user_id == current_user.id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dataset

@router.get("/{dataset_id}/preview", response_model=PreviewResponse)
async def preview_dataset(
    dataset_id: int,
    rows: int = Query(default=50, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Preview dataset (first N rows)"""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id, Dataset.user_id == current_user.id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    try:
        df = pd.read_csv(dataset.storage_path, nrows=rows)
        return PreviewResponse(
            columns=df.columns.tolist(),
            rows=df.head(rows).to_dict(orient='records'),
            total_rows=dataset.row_count or len(df)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading dataset: {str(e)}")
