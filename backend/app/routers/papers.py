from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
import os
import uuid
from datetime import datetime

from app.core.database import get_db
from app.models.user import User
from app.models.paper import Paper, PaperExtraction, PaperStatus
from app.routers.auth import get_current_user

router = APIRouter(prefix="/papers", tags=["Papers"])

UPLOAD_DIR = "./app/data/uploads/papers"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class PaperResponse(BaseModel):
    id: int
    filename: str
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class PaperDetailResponse(PaperResponse):
    storage_path: str

class ExtractionRequest(BaseModel):
    pass

class ExtractionResponse(BaseModel):
    id: int
    raw_text: str
    schema_json: str
    created_at: datetime
    
    class Config:
        from_attributes = True

@router.post("/upload", response_model=PaperResponse)
async def upload_paper(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a PDF paper"""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed"
        )
    
    # Generate unique filename
    paper_id = uuid.uuid4().hex[:12]
    filename = f"{paper_id}.pdf"
    storage_path = os.path.join(UPLOAD_DIR, filename)
    
    # Save file
    with open(storage_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # Create database record
    paper = Paper(
        user_id=current_user.id,
        filename=file.filename,
        storage_path=storage_path,
        status=PaperStatus.UPLOADED
    )
    db.add(paper)
    db.commit()
    db.refresh(paper)
    
    return paper

@router.get("", response_model=List[PaperResponse])
async def list_papers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all papers for current user"""
    papers = db.query(Paper).filter(Paper.user_id == current_user.id).order_by(Paper.created_at.desc()).all()
    return papers

@router.get("/{paper_id}", response_model=PaperDetailResponse)
async def get_paper(
    paper_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get paper details"""
    paper = db.query(Paper).filter(Paper.id == paper_id, Paper.user_id == current_user.id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    return paper

@router.post("/{paper_id}/extract", response_model=ExtractionResponse)
async def extract_paper(
    paper_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Extract content from paper (scaffold - placeholder implementation)"""
    paper = db.query(Paper).filter(Paper.id == paper_id, Paper.user_id == current_user.id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # TODO: Implement actual PDF extraction
    # For now, return placeholder
    raw_text = f"Extracted text from {paper.filename} (placeholder)"
    schema_json = '{"variables": [], "units": {}, "ranges": {}}'
    
    extraction = PaperExtraction(
        paper_id=paper.id,
        raw_text=raw_text,
        schema_json=schema_json
    )
    db.add(extraction)
    
    # Update paper status
    paper.status = PaperStatus.EXTRACTED
    db.commit()
    db.refresh(extraction)
    
    return extraction
