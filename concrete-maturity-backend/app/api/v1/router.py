"""Central v1 API router – aggregates all endpoint sub-routers."""

from fastapi import APIRouter

from app.api.v1.endpoints.alerts import router as alerts_router
from app.api.v1.endpoints.dashboard import router as dashboard_router
from app.api.v1.endpoints.mix_profiles import router as mix_profiles_router
from app.api.v1.endpoints.readings import router as readings_router
from app.api.v1.endpoints.sensors import router as sensors_router
from app.api.v1.endpoints.telemetry import router as telemetry_router
from app.api.v1.endpoints.thingsboard import router as thingsboard_router

api_router = APIRouter()

api_router.include_router(telemetry_router, prefix="/telemetry", tags=["Telemetry"])
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(sensors_router, prefix="/sensors", tags=["Sensors"])
api_router.include_router(readings_router, prefix="/readings", tags=["Readings"])
api_router.include_router(alerts_router, prefix="/alerts", tags=["Alerts"])
api_router.include_router(mix_profiles_router, prefix="/mix-profiles", tags=["Mix Profiles"])
api_router.include_router(thingsboard_router, prefix="/thingsboard", tags=["ThingsBoard"])
