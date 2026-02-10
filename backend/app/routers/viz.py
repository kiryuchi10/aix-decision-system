from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import FileResponse
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
from app.models.dataset import Dataset
from app.routers.auth import get_current_user
from app.models.user import User
from app.services.pipeline_service import run_step as pipeline_run_step, list_artifacts, get_summary
from app.services.etch_seed_sources import EtchSeedSource, resolve_mat_path
from app.services.mat_loader import load_mat_to_df
from app.services.viz_steps import run_eda_step, save_artifacts_for_step, list_preview_artifacts

router = APIRouter(prefix="/viz", tags=["Visualization Automation"])

BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
SEED_ETCH_DIR = BACKEND_ROOT / "app" / "data" / "seed" / "process_etch"

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

@router.post("/reports/spc/generate")
async def generate_spc_report(
    request: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate SPC Summary Report"""
    from app.services.report_renderer import render_spc_report
    
    spc_data = request.get("spc_data", {})
    report_meta = request.get("report_meta", {
        "title": "SPC Summary Report",
        "process": "Etch",
        "module": "SPC Center",
        "time_window": "Last 24 hours",
        "author": current_user.email,
        "version": "1.0"
    })
    data_meta = request.get("data_meta", {})
    
    filepath = render_spc_report(spc_data, report_meta, data_meta)
    
    return {
        "message": "SPC report generated successfully",
        "filepath": filepath,
        "filename": os.path.basename(filepath)
    }


@router.post("/reports/fdc/generate")
async def generate_fdc_report(
    request: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate FDC Alarm Review Report"""
    from app.services.report_renderer import render_fdc_report
    
    fdc_data = request.get("fdc_data", {})
    report_meta = request.get("report_meta", {
        "title": "FDC Alarm Review Report",
        "process": "Etch",
        "module": "FDC Sentinel",
        "time_window": "Last 24 hours",
        "author": current_user.email,
        "version": "1.0"
    })
    data_meta = request.get("data_meta", {})
    
    filepath = render_fdc_report(fdc_data, report_meta, data_meta)
    
    return {
        "message": "FDC report generated successfully",
        "filepath": filepath,
        "filename": os.path.basename(filepath)
    }


@router.post("/reports/rca/generate")
async def generate_rca_report(
    request: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate RCA (Root Cause Analysis) Report"""
    from app.services.report_renderer import render_rca_report
    
    rca_data = request.get("rca_data", {})
    report_meta = request.get("report_meta", {
        "title": "Root Cause Analysis Report",
        "process": "Etch",
        "module": "Quality Analysis",
        "time_window": "Incident Analysis",
        "author": current_user.email,
        "version": "1.0"
    })
    data_meta = request.get("data_meta", {})
    
    filepath = render_rca_report(rca_data, report_meta, data_meta)
    
    return {
        "message": "RCA report generated successfully",
        "filepath": filepath,
        "filename": os.path.basename(filepath)
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
    
    return FileResponse(
        report.report_path,
        media_type="application/octet-stream",
        filename=f"report_{report_id}.{report.report_type.lower()}"
    )


# ---------- Artifact-first pipeline (run-step, artifacts, summary) ----------

@router.post("/{dataset_id}/run-step")
async def viz_run_step(
    dataset_id: int,
    step: str = Query(..., description="raw|clean|eda|fe|pca|cluster|models|policy"),
    source: Optional[EtchSeedSource] = Query(None, description="MACHINE|OES|RFM for seed-based EDA"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Run pipeline step. With source loads seed .mat and runs EDA; else uses committed dataset file."""
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.user_id == current_user.id,
    ).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    if source is not None:
        if step != "eda":
            raise HTTPException(status_code=400, detail="Source-based run supports step=eda only")
        mat_path = resolve_mat_path(SEED_ETCH_DIR, source)
        if not mat_path.exists():
            raise HTTPException(status_code=404, detail="Missing seed file: " + mat_path.name)
        try:
            df = load_mat_to_df(str(mat_path))
        except Exception as e:
            raise HTTPException(status_code=400, detail="Failed to load .mat: " + str(e))
        summary, artifacts = run_eda_step(df, source=source.value)
        save_artifacts_for_step(
            dataset_id=dataset_id,
            step=step,
            source=source.value,
            summary=summary,
            artifacts=artifacts,
            base_dir=BACKEND_ROOT,
        )
        return {
            "status": "ok",
            "step": step,
            "source": source.value,
            "summary": summary,
            "artifact_count": len(artifacts),
        }

    if not getattr(dataset, "committed", False):
        raise HTTPException(
            status_code=403,
            detail="Dataset must be committed before running pipeline steps",
        )
    data_path = dataset.storage_path
    if not os.path.isabs(data_path):
        data_path = os.path.join(BACKEND_ROOT, data_path)
    if not os.path.exists(data_path):
        raise HTTPException(status_code=404, detail="Dataset file not found")
    result = pipeline_run_step(str(dataset_id), step, data_path)
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("error", "Step failed"))
    return result


@router.get("/{dataset_id}/summary")
async def viz_summary(
    dataset_id: int,
    step: Optional[str] = Query(None, description="Optional step filter"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Summary for dataset (and optional step)."""
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.user_id == current_user.id,
    ).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return get_summary(str(dataset_id), step)


@router.get("/{dataset_id}/artifacts")
async def viz_artifacts(
    dataset_id: int,
    step: Optional[str] = Query(None),
    source: Optional[str] = Query(None, description="MACHINE|OES|RFM to include preview artifacts"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List artifacts: [{ id, step, kind, title, url }]. When source is set, include preview/{dataset_id}/{step}/{source}."""
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.user_id == current_user.id,
    ).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    raw = list_artifacts(str(dataset_id), step)
    if source and step:
        preview = list_preview_artifacts(BACKEND_ROOT, dataset_id, step, source)
        for a in preview:
            path = a.get("path", "")
            if path and not any(r.get("path") == path for r in raw):
                raw.append(a)
    base_url = "/api/v1/viz/artifacts"
    artifacts = []
    for i, a in enumerate(raw):
        path = a.get("path", "")
        name = a.get("name", "")
        kind = a.get("type", "json")
        step_name = path.split("/")[-2] if "/" in path else (step or "")
        url = f"{base_url}/{path}" if path else ""
        artifacts.append({"id": f"{dataset_id}-{step_name}-{i}-{name}", "kind": kind, "title": name, "url": url})
    return {"artifacts": artifacts}


@router.get("/artifacts/{file_path:path}")
async def serve_artifact(
    file_path: str,
    current_user: User = Depends(get_current_user),
):
    """Serve artifact file for <img src> or download. Path relative to backend (e.g. app/data/...)."""
    full = (BACKEND_ROOT / file_path).resolve()
    try:
        full.relative_to(BACKEND_ROOT.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Invalid path")
    if not full.exists() or not full.is_file():
        raise HTTPException(status_code=404, detail="Artifact not found")
    media = "image/png" if full.suffix.lower() in (".png", ".jpg", ".jpeg") else "application/octet-stream"
    return FileResponse(full, media_type=media, filename=full.name)
