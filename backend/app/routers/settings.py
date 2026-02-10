"""
Settings Router
- Process Window (guardrails) — DB-backed
- Alarm Thresholds — DB-backed
- Integrations (Database, Streaming, Storage, Notifications) — DB-backed
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from datetime import datetime
import json

from app.core.database import get_db
from app.routers.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/settings", tags=["Settings"])


# ----- Pydantic models -----
class ProcessWindowRow(BaseModel):
    key: str
    unit: Optional[str] = None
    hardMin: float
    hardMax: float
    note: Optional[str] = None


class ProcessWindowResponse(BaseModel):
    updatedAt: Optional[str] = None
    rows: List[ProcessWindowRow]


class AlarmThresholds(BaseModel):
    enableWeco: bool = True
    sigmaThreshold: float = 3.0
    ewmaLambda: float = 0.2


class IntegrationConfig(BaseModel):
    type: str
    config_json: Optional[Dict[str, Any]] = None
    updatedAt: Optional[str] = None


class IntegrationUpdate(BaseModel):
    config_json: Dict[str, Any]


# Defaults (used when DB empty or table missing)
DEFAULT_ROWS = [
    ProcessWindowRow(key="pressure_torr", unit="Torr", hardMin=20.0, hardMax=60.0, note="Chamber pressure window"),
    ProcessWindowRow(key="bias_power_w", unit="W", hardMin=0.0, hardMax=500.0, note="RF bias power safety range"),
    ProcessWindowRow(key="chuck_temp_c", unit="°C", hardMin=10.0, hardMax=80.0),
    ProcessWindowRow(key="temperature", unit="°C", hardMin=840.0, hardMax=860.0, note="Process temperature range"),
]
DEFAULT_PROCESS_WINDOW = ProcessWindowResponse(updatedAt=datetime.utcnow().isoformat(), rows=DEFAULT_ROWS)
DEFAULT_ALARM_THRESHOLDS = AlarmThresholds(enableWeco=True, sigmaThreshold=3.0, ewmaLambda=0.2)


def _dialect(db: Session) -> str:
    return db.get_bind().dialect.name


def _ensure_settings_tables_sqlite(db: Session) -> None:
    if _dialect(db) != "sqlite":
        return
    for stmt in [
        """CREATE TABLE IF NOT EXISTS process_window (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT NOT NULL UNIQUE,
            unit TEXT,
            hard_min REAL NOT NULL,
            hard_max REAL NOT NULL,
            note TEXT,
            updated_at TEXT
        )""",
        """CREATE TABLE IF NOT EXISTS alarm_thresholds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            enable_weco INTEGER NOT NULL DEFAULT 1,
            sigma_threshold REAL NOT NULL DEFAULT 3.0,
            ewma_lambda REAL NOT NULL DEFAULT 0.2,
            updated_at TEXT
        )""",
        """CREATE TABLE IF NOT EXISTS integrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL UNIQUE,
            config_json TEXT,
            updated_at TEXT
        )""",
    ]:
        try:
            db.execute(text(stmt))
            db.commit()
        except Exception:
            db.rollback()


# ----- Process Window -----
@router.get("/process-window", response_model=ProcessWindowResponse)
async def get_process_window(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get process window guardrails from DB."""
    _ensure_settings_tables_sqlite(db)
    try:
        result = db.execute(text("SELECT key, unit, hard_min, hard_max, note FROM process_window ORDER BY key"))
        rows = []
        for r in result:
            rows.append(ProcessWindowRow(
                key=r[0],
                unit=r[1],
                hardMin=float(r[2]),
                hardMax=float(r[3]),
                note=r[4],
            ))
        if not rows:
            return DEFAULT_PROCESS_WINDOW
        updated = db.execute(text("SELECT MAX(updated_at) FROM process_window")).scalar()
        return ProcessWindowResponse(updatedAt=updated, rows=rows)
    except Exception:
        return DEFAULT_PROCESS_WINDOW


@router.post("/process-window", response_model=dict)
async def save_process_window(
    payload: ProcessWindowResponse,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Save process window guardrails to DB (replace all rows)."""
    if not payload.rows:
        raise HTTPException(status_code=400, detail="Process window rows cannot be empty")
    for row in payload.rows:
        if row.hardMin >= row.hardMax:
            raise HTTPException(status_code=400, detail=f"Invalid range for {row.key}: min must be less than max")

    _ensure_settings_tables_sqlite(db)
    dialect = _dialect(db)
    now = datetime.utcnow().isoformat()
    try:
        db.execute(text("DELETE FROM process_window"))
        for row in payload.rows:
            if dialect == "sqlite":
                db.execute(
                    text(
                        "INSERT INTO process_window (key, unit, hard_min, hard_max, note, updated_at) "
                        "VALUES (:key, :unit, :hard_min, :hard_max, :note, :updated_at)"
                    ),
                    {
                        "key": row.key,
                        "unit": row.unit,
                        "hard_min": row.hardMin,
                        "hard_max": row.hardMax,
                        "note": row.note,
                        "updated_at": now,
                    },
                )
            else:
                db.execute(
                    text(
                        "INSERT INTO process_window (`key`, unit, hard_min, hard_max, note, updated_at) "
                        "VALUES (:key, :unit, :hard_min, :hard_max, :note, :updated_at)"
                    ),
                    {
                        "key": row.key,
                        "unit": row.unit,
                        "hard_min": row.hardMin,
                        "hard_max": row.hardMax,
                        "note": row.note,
                        "updated_at": now,
                    },
                )
        db.commit()
        return {"ok": True, "message": "Process window saved successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ----- Alarm Thresholds -----
@router.get("/alarm-thresholds", response_model=AlarmThresholds)
async def get_alarm_thresholds(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get alarm thresholds from DB."""
    _ensure_settings_tables_sqlite(db)
    try:
        result = db.execute(text("SELECT enable_weco, sigma_threshold, ewma_lambda FROM alarm_thresholds LIMIT 1"))
        row = result.fetchone()
        if row:
            return AlarmThresholds(
                enableWeco=bool(row[0]),
                sigmaThreshold=float(row[1]),
                ewmaLambda=float(row[2]),
            )
        # Seed single row
        db.execute(
            text(
                "INSERT INTO alarm_thresholds (enable_weco, sigma_threshold, ewma_lambda) VALUES (1, 3.0, 0.2)"
            )
        )
        db.commit()
        return DEFAULT_ALARM_THRESHOLDS
    except Exception:
        return DEFAULT_ALARM_THRESHOLDS


@router.post("/alarm-thresholds", response_model=dict)
async def save_alarm_thresholds(
    payload: AlarmThresholds,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Save alarm thresholds to DB."""
    if payload.sigmaThreshold < 0:
        raise HTTPException(status_code=400, detail="Sigma threshold must be positive")
    if not (0 < payload.ewmaLambda < 1):
        raise HTTPException(status_code=400, detail="EWMA lambda must be between 0 and 1")

    _ensure_settings_tables_sqlite(db)
    try:
        dialect = _dialect(db)
        enable_int = 1 if payload.enableWeco else 0
        if dialect == "sqlite":
            db.execute(text("DELETE FROM alarm_thresholds"))
            db.execute(
                text(
                    "INSERT INTO alarm_thresholds (enable_weco, sigma_threshold, ewma_lambda) "
                    "VALUES (:ew, :st, :el)"
                ),
                {"ew": enable_int, "st": payload.sigmaThreshold, "el": payload.ewmaLambda},
            )
        else:
            db.execute(
                text(
                    "INSERT INTO alarm_thresholds (id, enable_weco, sigma_threshold, ewma_lambda) "
                    "VALUES (1, :ew, :st, :el) ON DUPLICATE KEY UPDATE "
                    "enable_weco=VALUES(enable_weco), sigma_threshold=VALUES(sigma_threshold), ewma_lambda=VALUES(ewma_lambda)"
                ),
                {"ew": enable_int, "st": payload.sigmaThreshold, "el": payload.ewmaLambda},
            )
        db.commit()
        return {"ok": True, "message": "Alarm thresholds saved successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ----- Integrations -----
INTEGRATION_TYPES = ["database", "streaming", "storage", "notifications"]


@router.get("/integrations", response_model=List[IntegrationConfig])
async def list_integrations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all integration configs (Database, Streaming, Storage, Notifications)."""
    _ensure_settings_tables_sqlite(db)
    try:
        result = db.execute(text("SELECT type, config_json, updated_at FROM integrations ORDER BY type"))
        rows = list(result)
        if not rows:
            for t in INTEGRATION_TYPES:
                try:
                    db.execute(
                        text("INSERT INTO integrations (type) VALUES (:type)"),
                        {"type": t},
                    )
                except Exception:
                    pass
            db.commit()
            result = db.execute(text("SELECT type, config_json, updated_at FROM integrations ORDER BY type"))
            rows = list(result)
        out = []
        for r in rows:
            config = json.loads(r[1]) if r[1] else None
            out.append(IntegrationConfig(type=r[0], config_json=config, updatedAt=str(r[2]) if r[2] else None))
        return out
    except Exception:
        return [IntegrationConfig(type=t, config_json=None) for t in INTEGRATION_TYPES]


@router.get("/integrations/{integration_type}", response_model=IntegrationConfig)
async def get_integration(
    integration_type: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get one integration config by type."""
    if integration_type not in INTEGRATION_TYPES:
        raise HTTPException(status_code=404, detail="Integration type not found")
    _ensure_settings_tables_sqlite(db)
    try:
        result = db.execute(
            text("SELECT type, config_json, updated_at FROM integrations WHERE type = :t"),
            {"t": integration_type},
        )
        row = result.fetchone()
        if row:
            config = json.loads(row[1]) if row[1] else None
            return IntegrationConfig(type=row[0], config_json=config, updatedAt=str(row[2]) if row[2] else None)
        return IntegrationConfig(type=integration_type, config_json=None)
    except Exception:
        return IntegrationConfig(type=integration_type, config_json=None)


@router.put("/integrations/{integration_type}", response_model=dict)
async def update_integration(
    integration_type: str,
    payload: IntegrationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create or update integration config (Database, Streaming, Storage, Notifications)."""
    if integration_type not in INTEGRATION_TYPES:
        raise HTTPException(status_code=404, detail="Integration type not found")
    _ensure_settings_tables_sqlite(db)
    dialect = _dialect(db)
    now = datetime.utcnow().isoformat()
    config_str = json.dumps(payload.config_json)
    try:
        if dialect == "sqlite":
            db.execute(
                text(
                    "INSERT INTO integrations (type, config_json, updated_at) VALUES (:type, :config, :at) "
                    "ON CONFLICT(type) DO UPDATE SET config_json=:config, updated_at=:at"
                ),
                {"type": integration_type, "config": config_str, "at": now},
            )
        else:
            db.execute(
                text(
                    "INSERT INTO integrations (type, config_json, updated_at) VALUES (:type, :config, :at) "
                    "ON DUPLICATE KEY UPDATE config_json=VALUES(config_json), updated_at=VALUES(updated_at)"
                ),
                {"type": integration_type, "config": config_str, "at": now},
            )
        db.commit()
        return {"ok": True, "message": f"Integration {integration_type} updated"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
