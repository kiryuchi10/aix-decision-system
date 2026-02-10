from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field
import os
import json
import csv
import io
from pathlib import Path

from app.core.database import get_db
from app.models.user import User, UserRole
from app.models.seed import SeedCatalog, SourceType
from app.routers.auth import get_current_user
from app.services.mat_reader import load_mat, mat_to_wafer_feature_df

router = APIRouter(prefix="/seeds", tags=["Seeds"])

# Resolve seed base dir relative to app (backend/app)
_APP_DIR = Path(__file__).resolve().parent.parent
SEED_BASE_DIR = str(_APP_DIR / "data" / "seed")
SEED_ROOT = Path(SEED_BASE_DIR)

class SeedResponse(BaseModel):
    id: int
    process_type: str
    seed_path: str
    source_type: str
    created_at: str
    
    class Config:
        from_attributes = True

class RegisterSeedRequest(BaseModel):
    seed_path: str
    process_type: str
    schema_data: dict = Field(..., alias="schema_json", serialization_alias="schema_json")

@router.get("", response_model=List[SeedResponse])
async def list_seeds(
    process_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Scan and list seeds from filesystem and DB"""
    # Query from database
    query = db.query(SeedCatalog)
    if process_type:
        query = query.filter(SeedCatalog.process_type == process_type)
    db_seeds = query.order_by(SeedCatalog.created_at.desc()).all()
    
    # Also scan filesystem
    filesystem_seeds = []
    if os.path.exists(SEED_BASE_DIR):
        for root, dirs, files in os.walk(SEED_BASE_DIR):
            # Look for schema.json files
            if "schema.json" in files:
                rel_path = os.path.relpath(root, SEED_BASE_DIR)
                schema_path = os.path.join(root, "schema.json")
                try:
                    with open(schema_path, "r") as f:
                        schema_data = json.load(f)
                        process_type_from_schema = schema_data.get("process_type", "unknown")
                        filesystem_seeds.append({
                            "process_type": process_type_from_schema,
                            "seed_path": rel_path,
                            "source_type": "filesystem"
                        })
                except:
                    pass
    
    # Return DB seeds (filesystem seeds can be registered via POST /register)
    return db_seeds

@router.post("/register", response_model=SeedResponse)
async def register_seed(
    request: RegisterSeedRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Register a seed folder in the catalog"""
    # Check admin permission
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can register seeds"
        )
    
    # Validate path exists
    full_path = os.path.join(SEED_BASE_DIR, request.seed_path)
    schema_path = os.path.join(full_path, "schema.json")
    if not os.path.exists(schema_path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Schema file not found at {schema_path}"
        )
    
    # Create database record
    seed = SeedCatalog(
        process_type=request.process_type,
        seed_path=request.seed_path,
        schema_json=json.dumps(request.schema_data),
        source_type=SourceType.SYNTHETIC,  # Default, can be updated
        source_id=None
    )
    db.add(seed)
    db.commit()
    db.refresh(seed)
    
    return seed


class SeedFolderInfo(BaseModel):
    id: str
    path: str
    process_type: str
    row_count: Optional[int] = None
    columns: List[str] = []
    has_csv: bool = False
    has_schema: bool = False
    has_mat: bool = False


def _safe_join_seed(rel_path: str) -> Path:
    """Resolve seed subpath; disallow path traversal."""
    p = (SEED_ROOT / rel_path).resolve()
    if SEED_ROOT.resolve() not in p.parents and p != SEED_ROOT.resolve():
        raise HTTPException(status_code=403, detail="Invalid seed path")
    return p


@router.get("/folders", response_model=List[SeedFolderInfo])
async def list_seed_folders(
    process_type: Optional[str] = None,
    current_user: Any = Depends(get_current_user),
):
    """List seed folders (schema.json, data.csv, or .mat) under app/data/seed for Process Analysis."""
    folders: List[SeedFolderInfo] = []
    base = Path(SEED_BASE_DIR)
    if not base.exists():
        return folders
    # Top-level dirs only (e.g. process_etch)
    for d in sorted([p for p in base.iterdir() if p.is_dir()]):
        rel_str = d.name
        has_schema = (d / "schema.json").exists()
        has_csv = (d / "data.csv").exists()
        mats = list(d.glob("*.mat"))
        has_mat = bool(mats)
        if not (has_schema or has_csv or has_mat):
            continue
        process_type_from_schema = "etch"  # default for .mat etch data
        columns: List[str] = []
        row_count: Optional[int] = None
        if has_schema:
            try:
                with open(d / "schema.json", "r") as f:
                    schema_data = json.load(f)
                    process_type_from_schema = schema_data.get("process_type", "etch")
                    columns = schema_data.get("columns", [])[:50]
                    row_count = schema_data.get("row_count")
            except Exception:
                pass
        if has_mat and (row_count is None or not columns):
            try:
                df = mat_to_wafer_feature_df(mats[0], limit=200)
                row_count = int(len(df))
                columns = df.columns.tolist()[:50]
            except Exception:
                pass
        if process_type and process_type_from_schema != process_type:
            continue
        folders.append(SeedFolderInfo(
            id=rel_str.replace("/", "_") or "root",
            path=rel_str,
            process_type=process_type_from_schema,
            row_count=row_count,
            columns=columns,
            has_csv=has_csv,
            has_schema=has_schema,
            has_mat=has_mat,
        ))
    return folders


@router.get("/folders/{path:path}/schema")
async def get_seed_schema(path: str):
    """Get schema.json for a seed folder."""
    full = _safe_join_seed(path)
    if not full.is_dir():
        raise HTTPException(status_code=404, detail="Seed folder not found")
    schema_file = full / "schema.json"
    if not schema_file.exists():
        raise HTTPException(status_code=404, detail="schema.json not found")
    with open(schema_file, "r") as f:
        return json.load(f)


@router.get("/folders/{path:path}/data")
async def get_seed_folder_data(
    path: str,
    limit: int = Query(default=5000, ge=100, le=20000),
    current_user: Any = Depends(get_current_user),
):
    """Get seed folder data as JSON: data.csv if present, else .mat as wafer-level feature table (for Process Analysis)."""
    full = _safe_join_seed(path)
    if not full.is_dir():
        raise HTTPException(status_code=404, detail="Seed folder not found")
    data_file = full / "data.csv"
    if data_file.exists():
        rows: List[Dict[str, Any]] = []
        with open(data_file, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            cols = reader.fieldnames or []
            for i, row in enumerate(reader):
                if i >= limit:
                    break
                rows.append(row)
        return {"columns": cols, "rows": rows, "row_count": len(rows)}
    mats = list(full.glob("*.mat"))
    if not mats:
        raise HTTPException(status_code=404, detail="No data.csv or .mat files in this seed folder")
    # Prefer MACHINE_Data.mat
    mats_sorted = sorted(mats, key=lambda p: (p.name != "MACHINE_Data.mat", p.name))
    try:
        df = mat_to_wafer_feature_df(mats_sorted[0], limit=limit)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Unsupported .mat schema: {e!s}")
    columns = df.columns.tolist()
    rows = df.to_dict(orient="records")
    return {"columns": columns, "rows": rows, "row_count": len(rows)}
