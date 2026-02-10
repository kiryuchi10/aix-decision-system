"""
Interlock Response / STOP–Release Decision API
- FDC sensor data → AI decision → Release (간단 점검) or STOP (설비 수리)
- Stub for integration with FDC and Coupling Control
"""

from datetime import datetime
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.routers.auth import get_current_user
from app.models.user import User
from app.services.report_renderer import render_interlock_report

router = APIRouter(prefix="/interlock", tags=["Interlock / STOP-Release"])


class InterlockDecisionRequest(BaseModel):
    """Request body for STOP/Release decision (stub)."""
    sensor_snapshot: Optional[dict] = None  # FDC sensor values at decision time
    chamber_id: Optional[str] = None
    recipe_id: Optional[str] = None
    interlock_detected: bool = True


class InterlockDecisionResponse(BaseModel):
    """AI decision: NORMAL, RELEASE, or STOP."""
    decision: Literal["NORMAL", "RELEASE", "STOP"]
    confidence: float
    reason_ko: Optional[str] = None
    reason_en: Optional[str] = None
    suggested_action_ko: Optional[str] = None
    suggested_action_en: Optional[str] = None
    timestamp: str


@router.post("/decision", response_model=InterlockDecisionResponse)
async def post_interlock_decision(
    body: InterlockDecisionRequest,
    current_user: User = Depends(get_current_user),
):
    """
    STOP/Release 판정 AI (stub).
    In production: run LSTM/Transformer or rule-based model on FDC snapshot.
    """
    # Stub logic: simple rule for demo
    if not body.interlock_detected:
        return InterlockDecisionResponse(
            decision="NORMAL",
            confidence=1.0,
            reason_ko="Interlock 미발생",
            reason_en="No interlock detected",
            timestamp=datetime.utcnow().isoformat(),
        )
    # Simulate: 70% Release (간단 점검), 30% STOP (설비 수리)
    import random
    r = random.random()
    if r < 0.7:
        return InterlockDecisionResponse(
            decision="RELEASE",
            confidence=0.85,
            reason_ko="임계치 근접, 간단 점검 후 가동 가능",
            reason_en="Near threshold; release after quick check",
            suggested_action_ko="간단한 점검 후 Release",
            suggested_action_en="Release after simple check",
            timestamp=datetime.utcnow().isoformat(),
        )
    return InterlockDecisionResponse(
        decision="STOP",
        confidence=0.9,
        reason_ko="설비 이상 의심, 수리 필요",
        reason_en="Equipment fault suspected; repair required",
        suggested_action_ko="STOP 후 설비 수리",
        suggested_action_en="STOP and equipment repair",
        timestamp=datetime.utcnow().isoformat(),
    )


@router.get("/status")
async def get_interlock_status(current_user: User = Depends(get_current_user)):
    """Aggregate status for dashboard (stub)."""
    return {
        "events_24h": 12,
        "release_count": 8,
        "stop_count": 4,
        "downtime_saved_hr": 2.5,
        "last_decision_at": datetime.utcnow().isoformat(),
    }


class InterlockReportRequest(BaseModel):
    title: Optional[str] = "Interlock Response Report"
    process: Optional[str] = "Etch"
    time_window: Optional[str] = "24h"


@router.post("/reports/generate")
async def generate_interlock_report(
    body: Optional[InterlockReportRequest] = None,
    current_user: User = Depends(get_current_user),
):
    """Generate interlock report (HTML) with figures + KPI tables."""
    body = body or InterlockReportRequest()
    interlock_data = {
        "events_24h": 12,
        "release_count": 8,
        "stop_count": 4,
        "downtime_saved_hr": 2.5,
        "actions": [
            "Review STOP events for root cause.",
            "Calibrate thresholds if Release rate is too high.",
        ],
    }
    report_meta = {
        "title": body.title or "Interlock Response Report",
        "process": body.process or "Etch",
        "module": "Interlock / STOP-Release",
        "time_window": body.time_window or "24h",
        "author": getattr(current_user, "username", "system"),
        "version": "1.0",
        "context": "FDC sensor data → STOP/Release Decision AI → Reduce equipment downtime.",
    }
    filepath = render_interlock_report(interlock_data, report_meta)
    return {"filepath": filepath, "message": "Report generated."}
