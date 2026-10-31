"""
Concrete Maturity API – FastAPI Application Entry Point.

Initialises middleware (CORS), mounts the v1 API router, creates
database tables on startup, and exposes the Uvicorn-compatible ASGI app.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from pathlib import Path

from fastapi import Depends
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.router import api_router
from app.core.config import settings
from app.database.connection import get_db, init_db
from app.models.sensor_reading import SensorReading


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown lifecycle events."""
    await init_db()
    yield
    # Teardown logic can go here (e.g., close connection pools)


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Real-time concrete curing monitoring API. "
        "Ingests telemetry from ESP32 via ThingsBoard and "
        "provides dashboards using the Nurse-Saul maturity method."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ─── CORS Middleware ───────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?|https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ──────────────────────────────────────────────────────────────────
app.include_router(api_router, prefix="/api/v1")


@app.get("/api/latest", tags=["Dashboard Compatibility"])
async def get_latest_direct(db: AsyncSession = Depends(get_db)):
    """
    Direct polling endpoint for the Concrete Maturity Meter frontend dashboard.
    Returns the latest temperature and Nurse-Saul maturity values.
    """
    result = await db.execute(
        select(SensorReading).order_by(SensorReading.received_at.desc()).limit(1)
    )
    reading = result.scalar_one_or_none()
    if reading is None:
        return {"temperature_c": 25.0, "status": "waiting_for_telemetry"}
    return {
        "temperature_c": reading.temperature_c,
        "maturity_c_hour": reading.maturity_c_hour,
        "simulated_hours": reading.simulated_hours,
        "sensor_id": reading.sensor_id,
        "sensor_status": reading.sensor_status,
        "data_mode": reading.data_mode,
        "recorded_at": reading.recorded_at.isoformat(),
    }


# ─── Static Frontend Mount ───────────────────────────────────────────────────
_frontend_dir = Path(__file__).resolve().parent.parent.parent / "Concrete-Maturity-Meter"
if _frontend_dir.is_dir():
    app.mount("/dashboard", StaticFiles(directory=str(_frontend_dir), html=True), name="dashboard")


@app.get("/", tags=["Root"])
async def root():
    """Health probe for the API root."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "dashboard": "/dashboard",
        "status": "ok",
    }
