# app/main.py
"""
FastAPI entrypoint:
- Loads settings from .env via Settings
- Creates DB tables (dev)
- Registers routers
- Enables CORS for React dev servers
- Runs WebSocket for real-time sensor stream simulation
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
from datetime import datetime
import json

from .routers import fdc, doe, ml_pipeline, coupling, recommendations, auth, data_management
from .routers.dashboard import router as dashboard_router

from .core.database import engine, Base
from .core.websocket_manager import WebSocketManager

# Create FastAPI app FIRST
app = FastAPI(
    title="AiX Decision System",
    description="Adaptive DoE Planner + FDC Drift Sentinel Integration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware (React runs on different port => browser blocks without this)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables (DEV ONLY)
# In production, prefer Alembic migrations instead of create_all()
Base.metadata.create_all(bind=engine)

# WebSocket manager for pushing real-time points to clients
websocket_manager = WebSocketManager()

# Include routers (HTTP endpoints)
app.include_router(auth.router, prefix="/api/v1")
app.include_router(fdc.router, prefix="/api/v1")
app.include_router(doe.router, prefix="/api/v1")
app.include_router(ml_pipeline.router, prefix="/api/v1")
app.include_router(coupling.router, prefix="/api/v1")
app.include_router(recommendations.router, prefix="/api/v1")
app.include_router(data_management.router, prefix="/api/v1")

# Dashboard endpoints
app.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])


@app.get("/")
async def root():
    return {
        "message": "AiX Decision System API",
        "version": "1.0.0",
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "database": "connected",  # TODO: add real check later
            "redis": "optional",
            "ml_pipeline": "ready"
        }
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            await websocket_manager.send_personal_message(
                json.dumps({"type": "echo", "data": message}),
                websocket
            )
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)


@app.on_event("startup")
async def startup_event():
    # Start background tasks
    asyncio.create_task(simulate_sensor_data())


async def simulate_sensor_data():
    """Simulate real-time sensor data for demo purposes."""
    import random
    while True:
        sensor_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "temperature": round(850 + random.uniform(-10, 10), 2),
            "pressure": round(2.5 + random.uniform(-0.2, 0.2), 3),
            "gas_flow": round(100 + random.uniform(-5, 5), 1),
            "power": round(1500 + random.uniform(-50, 50), 1)
        }

        await websocket_manager.broadcast(json.dumps({
            "type": "sensor_data",
            "data": sensor_data
        }))

        await asyncio.sleep(1)


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
