from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import pandas as pd
import json
import uuid
import os
from datetime import datetime

from app.core.database import get_db
from app.models.viz import VizSource, VizChartRecipe, VizReport
from app.routers.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/viz", tags=["Visualization Automation"])

UPLOAD_DIR = "./app/data/uploads/viz"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class ColumnMapRequest(BaseModel):
    source_id: str
    column_map: dict  # {original_column: mapped_column}

class ChartPreviewRequest(BaseModel):
    source_id: str
    recipe_id: Optional[str] = None
    preset_type: Optional[str] = None  # ETCH_CORE, CHAMBER_HEALTH, etc.

class ChartPreviewResponse(BaseModel):
    recipe_id: str
    chart_config: dict
    data_sample: List[dict]
    required_columns: List[str]

class ReportGenerateRequest(BaseModel):
    source_id: str
    recipe_id: str
    report_type: str = "HTML"  # HTML, PDF
    title: Optional[str] = None

@router.post("/sources/upload")
async def upload_source(
    file: UploadFile = File(...),
    name: Optional[str] = None,
    process_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload data source file"""
    source_id = uuid.uuid4().hex[:12]
    
    # Save file
    file_path = os.path.join(UPLOAD_DIR, f"{source_id}_{file.filename}")
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # Read and analyze file
    try:
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file.filename.endswith('.parquet'):
            df = pd.read_parquet(file_path)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format")
        
        # Create schema
        schema = {
            "columns": list(df.columns),
            "dtypes": df.dtypes.astype(str).to_dict(),
            "row_count": len(df),
            "sample_data": df.head(10).to_dict(orient="records")
        }
        
        # Create source record
        source = VizSource(
            source_id=source_id,
            source_type="UPLOAD",
            source_path=file_path,
            column_map={},
            schema_json=schema,
            name=name or file.filename,
            process_type=process_type or "etch",
            user_id=current_user.id
        )
        db.add(source)
        db.commit()
        db.refresh(source)
        
        return {
            "source_id": source_id,
            "schema": schema,
            "message": "File uploaded successfully"
        }
    except Exception as e:
        os.remove(file_path)
        raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")

@router.post("/column-map")
async def save_column_map(
    request: ColumnMapRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Save column mapping for a source"""
    source = db.query(VizSource).filter(VizSource.source_id == request.source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    source.column_map = request.column_map
    db.commit()
    
    return {
        "source_id": request.source_id,
        "column_map": request.column_map,
        "message": "Column mapping saved"
    }

@router.post("/charts/preview", response_model=ChartPreviewResponse)
async def preview_charts(
    request: ChartPreviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Preview chart recipe with data sample"""
    source = db.query(VizSource).filter(VizSource.source_id == request.source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    # Get or create recipe
    if request.recipe_id:
        recipe = db.query(VizChartRecipe).filter(VizChartRecipe.recipe_id == request.recipe_id).first()
    elif request.preset_type:
        # Use preset
        recipe = db.query(VizChartRecipe).filter(
            VizChartRecipe.preset_type == request.preset_type,
            VizChartRecipe.is_public == True
        ).first()
    else:
        # Create default recipe
        recipe_id = uuid.uuid4().hex[:12]
        recipe = VizChartRecipe(
            recipe_id=recipe_id,
            name="Default Recipe",
            preset_type="ETCH_CORE",
            chart_config={
                "type": "multi_line",
                "subplots": 2,
                "x_axis": "timestamp",
                "y_axes": ["temperature", "pressure"]
            },
            required_columns=["timestamp", "temperature", "pressure"],
            is_public=True
        )
        db.add(recipe)
        db.commit()
        db.refresh(recipe)
    
    # Load data sample
    try:
        if source.source_path.endswith('.csv'):
            df = pd.read_csv(source.source_path, nrows=100)
        else:
            df = pd.DataFrame()
        
        # Apply column mapping
        if source.column_map:
            df = df.rename(columns=source.column_map)
        
        data_sample = df.head(20).to_dict(orient="records")
    except Exception as e:
        data_sample = []
    
    return ChartPreviewResponse(
        recipe_id=recipe.recipe_id,
        chart_config=recipe.chart_config,
        data_sample=data_sample,
        required_columns=recipe.required_columns or []
    )

@router.post("/reports/generate")
async def generate_report(
    request: ReportGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate visualization report"""
    source = db.query(VizSource).filter(VizSource.source_id == request.source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    recipe = db.query(VizChartRecipe).filter(VizChartRecipe.recipe_id == request.recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    report_id = uuid.uuid4().hex[:12]
    
    # Create report record
    report = VizReport(
        report_id=report_id,
        source_id=request.source_id,
        recipe_id=request.recipe_id,
        report_type=request.report_type,
        title=request.title or f"Report {report_id}",
        status="GENERATING",
        user_id=current_user.id
    )
    db.add(report)
    db.commit()
    
    # TODO: Actually generate report (HTML/PDF)
    # For now, create placeholder
    report_path = os.path.join(UPLOAD_DIR, f"report_{report_id}.html")
    with open(report_path, "w") as f:
        f.write(f"<html><body><h1>{report.title}</h1><p>Report generated at {datetime.utcnow()}</p></body></html>")
    
    report.report_path = report_path
    report.status = "COMPLETED"
    report.completed_at = datetime.utcnow()
    db.commit()
    
    return {
        "report_id": report_id,
        "status": "COMPLETED",
        "download_url": f"/api/v1/viz/reports/{report_id}/download"
    }

@router.get("/reports/{report_id}/download")
async def download_report(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download generated report"""
    report = db.query(VizReport).filter(VizReport.report_id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if report.status != "COMPLETED":
        raise HTTPException(status_code=400, detail="Report not ready")
    
    if not os.path.exists(report.report_path):
        raise HTTPException(status_code=404, detail="Report file not found")
    
    from fastapi.responses import FileResponse
    return FileResponse(
        report.report_path,
        media_type="application/octet-stream",
        filename=f"report_{report_id}.{report.report_type.lower()}"
    )
