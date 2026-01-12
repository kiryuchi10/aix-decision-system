from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import os
import json
from pathlib import Path

from app.core.database import get_db
from app.models.user import User, UserRole
from app.models.seed import SeedCatalog, SourceType
from app.routers.auth import get_current_user

router = APIRouter(prefix="/seeds", tags=["Seeds"])

SEED_BASE_DIR = "./app/data/seed"

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
    schema_json: dict

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
        schema_json=json.dumps(request.schema_json),
        source_type=SourceType.SYNTHETIC,  # Default, can be updated
        source_id=None
    )
    db.add(seed)
    db.commit()
    db.refresh(seed)
    
    return seed
