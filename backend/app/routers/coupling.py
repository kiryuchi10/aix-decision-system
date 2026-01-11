from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter(prefix="/coupling", tags=["Coupling Service"])

class CouplingStatus(BaseModel):
    is_active: bool
    mode: str  # MANUAL, SEMI_AUTO, FULL_AUTO
    last_action: Optional[str] = None
    last_action_time: Optional[datetime] = None

class CouplingAction(BaseModel):
    id: str
    trigger_type: str  # FDC_ALARM, DOE_COMPLETION
    action_type: str  # PARAMETER_ADJUSTMENT, EXPERIMENT_GENERATION
    parameters: dict
    confidence: float
    requires_approval: bool
    status: str  # PENDING, APPROVED, EXECUTED, REJECTED

@router.get("/status")
async def get_coupling_status() -> CouplingStatus:
    """Get coupling system status"""
    return CouplingStatus(
        is_active=True,
        mode="SEMI_AUTO",
        last_action="Parameter adjustment for temperature drift",
        last_action_time=datetime.utcnow()
    )

@router.get("/actions/pending")
async def get_pending_actions() -> List[CouplingAction]:
    """Get pending coupling actions"""
    return [
        CouplingAction(
            id="ACT-001",
            trigger_type="FDC_ALARM",
            action_type="PARAMETER_ADJUSTMENT",
            parameters={
                "temperature": {"current": 865.2, "recommended": 850.0},
                "confidence": 0.87,
                "expected_improvement": 4.2
            },
            confidence=0.87,
            requires_approval=True,
            status="PENDING"
        )
    ]

@router.post("/actions/{action_id}/approve")
async def approve_action(action_id: str):
    """Approve a coupling action"""
    return {
        "status": "success",
        "message": f"Action {action_id} approved and executed",
        "execution_time": datetime.utcnow().isoformat()
    }

@router.post("/actions/{action_id}/reject")
async def reject_action(action_id: str, reason: str = ""):
    """Reject a coupling action"""
    return {
        "status": "success",
        "message": f"Action {action_id} rejected",
        "reason": reason,
        "timestamp": datetime.utcnow().isoformat()
    }