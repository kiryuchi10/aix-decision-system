from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
import os
import uuid
import pandas as pd
import json
from datetime import datetime

from app.core.database import get_db
from app.models.user import User, UserRole
from app.models.synthetic import SyntheticRun
from app.routers.auth import get_current_user
from app.services.generator.etch_generator import EtchDataGenerator

router = APIRouter(prefix="/generate", tags=["Generator"])

OUTPUT_DIR = "./app/data/seed"
os.makedirs(OUTPUT_DIR, exist_ok=True)

class GenerateRequest(BaseModel):
    processType: str
    template: Optional[str] = None
    nRuns: int = 100
    timeSeries: bool = False
    saveAsSeedFolder: bool = False
    include_drift: bool = False
    include_step_change: bool = False
    include_intermittent: bool = False

class GenerateResponse(BaseModel):
    run_id: int
    output_path: str
    message: str

class TemplateResponse(BaseModel):
    process_type: str
    templates: List[str]

@router.post("", response_model=GenerateResponse)
async def generate_synthetic(
    request: GenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate synthetic data"""
    # Check permission (optional restriction)
    # if current_user.role != UserRole.ADMIN:
    #     raise HTTPException(status_code=403, detail="Permission denied")
    
    run_id = uuid.uuid4().hex[:12]
    
    # Generate data based on process type
    if request.processType.lower() == "etch":
        # Use Etch data generator
        generator = EtchDataGenerator(seed=42)
        df = generator.generate_dataset(
            n_runs=request.nRuns,
            include_drift=request.include_drift,
            include_step_change=request.include_step_change,
            include_intermittent=request.include_intermittent
        )
    else:
        # Generate generic data
        if request.timeSeries:
            dates = pd.date_range(start='2024-01-01', periods=request.nRuns, freq='H')
            data = {
                'timestamp': dates,
                'temperature': [850 + (i % 10) * 0.5 for i in range(request.nRuns)],
                'pressure': [2.5 + (i % 5) * 0.1 for i in range(request.nRuns)],
                'yield': [95 + (i % 3) for i in range(request.nRuns)]
            }
        else:
            data = {
                'run_id': [f"RUN-{i:04d}" for i in range(request.nRuns)],
                'temperature': [850 + (i % 10) * 0.5 for i in range(request.nRuns)],
                'pressure': [2.5 + (i % 5) * 0.1 for i in range(request.nRuns)],
                'yield': [95 + (i % 3) for i in range(request.nRuns)]
            }
        df = pd.DataFrame(data)
    
    # Save output
    if request.saveAsSeedFolder:
        seed_folder = os.path.join(OUTPUT_DIR, f"{request.processType}_{run_id}")
        os.makedirs(seed_folder, exist_ok=True)
        csv_path = os.path.join(seed_folder, "data.csv")
        schema_path = os.path.join(seed_folder, "schema.json")
        output_path = seed_folder
    else:
        csv_path = os.path.join(OUTPUT_DIR, f"{run_id}.csv")
        output_path = csv_path
    
    df.to_csv(csv_path, index=False)
    
    # Create schema.json
    schema = {
        "process_type": request.processType,
        "columns": list(df.columns),
        "dtypes": df.dtypes.astype(str).to_dict(),
        "row_count": len(df)
    }
    
    if request.saveAsSeedFolder:
        with open(schema_path, "w") as f:
            json.dump(schema, f, indent=2)
    
    # Save to database
    config = {
        "nRuns": request.nRuns,
        "timeSeries": request.timeSeries,
        "template": request.template
    }
    
    run = SyntheticRun(
        user_id=current_user.id,
        process_type=request.processType,
        template=request.template,
        config_json=json.dumps(config),
        output_seed_path=output_path if request.saveAsSeedFolder else None
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    
    return GenerateResponse(
        run_id=run.id,
        output_path=output_path,
        message=f"Synthetic data generated successfully. {len(df)} rows created."
    )

@router.get("/templates", response_model=TemplateResponse)
async def get_templates(
    processType: str,
    db: Session = Depends(get_db)
):
    """Get available templates for a process type"""
    if processType.lower() == "etch":
        templates = ["default", "with_drift", "with_step_change", "with_intermittent", "high_yield"]
    else:
        templates = ["default", "high_yield", "low_variance"]
    return TemplateResponse(
        process_type=processType,
        templates=templates
    )

@router.get("/presets")
async def get_presets():
    """Get process type presets (Etch, Depo, Litho)"""
    return {
        "etch": {
            "name": "Etch Process",
            "columns": EtchDataGenerator().generate_etch_schema()["columns"],
            "description": "Dry etch process with CF4/O2 chemistry"
        },
        "depo": {
            "name": "Deposition Process",
            "description": "CVD/PVD deposition process"
        },
        "litho": {
            "name": "Lithography Process",
            "description": "Photolithography process"
        }
    }

@router.post("/schema")
async def generate_schema(
    process_type: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate schema template for a process type"""
    if process_type.lower() == "etch":
        generator = EtchDataGenerator()
        schema = generator.generate_etch_schema()
        return schema
    else:
        raise HTTPException(status_code=400, detail=f"Process type {process_type} not supported")
