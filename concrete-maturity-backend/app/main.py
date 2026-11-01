"""
Concrete Maturity API – FastAPI Application Entry Point.

Initialises middleware (CORS), mounts the v1 API router, creates
database tables on startup, and exposes the Uvicorn-compatible ASGI app.
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
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
    Prioritizes live ThingsBoard telemetry if configured, otherwise falls back to database.
    """
    if settings.is_tb_configured:
        try:
            from app.services.thingsboard_service import ThingsBoardService
            tb_service = ThingsBoardService(settings)
            tb_latest = await tb_service.get_latest_telemetry()
            if tb_latest.get("temperature_c") is not None:
                return {
                    "temperature_c": tb_latest["temperature_c"],
                    "maturity_c_hour": tb_latest.get("maturity_c_hour", 0.0),
                    "simulated_hours": tb_latest.get("simulated_hours", 0.0),
                    "sensor_id": 1,
                    "sensor_status": tb_latest.get("sensor_status", True),
                    "data_mode": tb_latest.get("data_mode", "real"),
                    "recorded_at": tb_latest.get("recorded_at"),
                    "source": "thingsboard",
                    "discovered_keys": tb_latest.get("keys", []),
                    "raw_values": tb_latest.get("raw_values", {}),
                }
        except Exception:
            # Fall back to database query if ThingsBoard query encounters any error
            pass

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
        "source": "database",
    }


# ─── Static Frontend Mount ───────────────────────────────────────────────────
_frontend_dir = Path(__file__).resolve().parent.parent.parent / "Concrete-Maturity-Meter"
if _frontend_dir.is_dir():
    app.mount("/dashboard", StaticFiles(directory=str(_frontend_dir), html=True), name="dashboard")


@app.get("/thingsboard", tags=["Dashboard Compatibility"], include_in_schema=False)
async def redirect_to_thingsboard_dashboard():
    """Redirect to the dedicated ThingsBoard live dashboard."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/dashboard/thingsboard.html")


@app.get("/", tags=["Root"])
async def root():
    """Health probe for the API root."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "dashboard": "/dashboard",
        "thingsboard_dashboard": "/dashboard/thingsboard.html",
        "status": "ok",
    }

