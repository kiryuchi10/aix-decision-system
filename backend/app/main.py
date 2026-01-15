# app/main.py
"""
FastAPI entrypoint:
- Loads settings from .env via Settings (optional)
- Registers routers
- Enables CORS for React dev servers
- Runs WebSocket for real-time sensor stream simulation
- Provides /health with real DB ping
"""

from __future__ import annotations

import asyncio
import json
import os
import random
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .core.database import engine, Base
from .core.websocket_manager import WebSocketManager

# Core routers (always present)
from .routers import papers, datasets, seeds, generator, chat, auth, spc, viz, settings

# Optional routers (may not exist)
def _safe_import_router(module_path: str):
    try:
        module = __import__(module_path, fromlist=["router"])
        return getattr(module, "router", None)
    except (ImportError, ModuleNotFoundError):
        return None

fdc_router = _safe_import_router("app.routers.fdc")
doe_router = _safe_import_router("app.routers.doe")
ml_router = _safe_import_router("app.routers.ml_pipeline")
coupling_router = _safe_import_router("app.routers.coupling")
recommendations_router = _safe_import_router("app.routers.recommendations")
data_management_router = _safe_import_router("app.routers.data_management")
dashboard_router = _safe_import_router("app.routers.dashboard")

# WebSocket manager
websocket_manager = WebSocketManager()


def _env_bool(key: str, default: bool = False) -> bool:
    v = os.getenv(key)
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "y", "on")


def _env_float(key: str, default: float) -> float:
    v = os.getenv(key)
    try:
        return float(v) if v is not None else default
    except ValueError:
        return default


async def simulate_sensor_data(
    *,
    interval_s: float = 1.0,
    enabled: bool = True,
):
    """Simulate real-time sensor data for demo purposes."""
    if not enabled:
        return

    while True:
        sensor_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "temperature": round(850 + random.uniform(-10, 10), 2),
            "pressure": round(2.5 + random.uniform(-0.2, 0.2), 3),
            "gas_flow": round(100 + random.uniform(-5, 5), 1),
            "power": round(1500 + random.uniform(-50, 50), 1),
        }

        await websocket_manager.broadcast(
            json.dumps({"type": "sensor_data", "data": sensor_data})
        )
        await asyncio.sleep(interval_s)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Use lifespan instead of deprecated-ish on_event startup/shutdown patterns.
    - Optionally create tables in DEV
    - Start background simulation task (DEV/demo)
    """
    is_dev = _env_bool("AIX_DEV", default=True)
    create_tables = _env_bool("AIX_CREATE_TABLES", default=is_dev)

    if create_tables:
        # DEV only (prod = Alembic)
        Base.metadata.create_all(bind=engine)

    sim_enabled = _env_bool("AIX_SIMULATE_SENSOR", default=is_dev)
    sim_interval = _env_float("AIX_SIM_INTERVAL_S", default=1.0)

    task: Optional[asyncio.Task] = None
    if sim_enabled:
        task = asyncio.create_task(
            simulate_sensor_data(interval_s=sim_interval, enabled=True)
        )

    try:
        yield
    finally:
        if task:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task


app = FastAPI(
    title="AiX Decision System",
    description="Adaptive DoE Planner + FDC Drift Sentinel Integration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS (make this configurable later via settings)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(papers.router, prefix="/api/v1")
app.include_router(datasets.router, prefix="/api/v1")
app.include_router(seeds.router, prefix="/api/v1")
app.include_router(generator.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(spc.router, prefix="/api/v1")
app.include_router(viz.router, prefix="/api/v1")
app.include_router(settings.router, prefix="/api/v1")

# Optional routers
if fdc_router:
    app.include_router(fdc_router, prefix="/api/v1")
if doe_router:
    app.include_router(doe_router, prefix="/api/v1")
if ml_router:
    # if deps missing, router import 자체가 실패하므로 여기선 try 불필요
    app.include_router(ml_router, prefix="/api/v1")
if coupling_router:
    app.include_router(coupling_router, prefix="/api/v1")
if recommendations_router:
    app.include_router(recommendations_router, prefix="/api/v1")
if data_management_router:
    app.include_router(data_management_router, prefix="/api/v1")
if dashboard_router:
    app.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])


@app.get("/")
async def root():
    return {
        "message": "AiX Decision System API",
        "version": "1.0.0",
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/health")
async def health_check():
    # 실제 DB ping (간단 체크)
    db_ok = True
    try:
        # SQLAlchemy 2.0 style
        with engine.connect() as conn:
            conn.exec_driver_sql("SELECT 1")
    except Exception:
        db_ok = False

    return {
        "status": "healthy" if db_ok else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "database": "connected" if db_ok else "error",
            "redis": "optional",
            "ml_pipeline": "optional",
        },
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket_manager.connect(websocket)
    try:
        while True:
            raw = await websocket.receive_text()
            # 클라이언트가 보내는 메시지 표준: {"type": "...", "data": {...}}
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                msg = {"type": "raw", "data": raw}

            # echo
            await websocket_manager.send_personal_message(
                json.dumps({"type": "echo", "data": msg}),
                websocket,
            )
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
