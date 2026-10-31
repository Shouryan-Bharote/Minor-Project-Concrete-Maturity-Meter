"""Telemetry endpoints: webhook ingestion and health check."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_api_key
from app.database.connection import get_db
from app.schemas.telemetry import HealthResponse, TelemetryPayload, TelemetryResponse
from app.services.alert_service import AlertService
from app.services.telemetry_service import TelemetryService

router = APIRouter()


@router.post(
    "",
    response_model=TelemetryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest telemetry from ThingsBoard webhook",
    dependencies=[Depends(verify_api_key)],
)
async def ingest_telemetry(
    payload: TelemetryPayload,
    db: AsyncSession = Depends(get_db),
):
    """
    Receives a JSON telemetry payload forwarded by the ThingsBoard Rule Engine
    REST API Call Node and persists it as a SensorReading.

    Requires `X-API-Key` header matching `WEBHOOK_API_KEY`.
    """
    service = TelemetryService(db)
    alert_service = AlertService(db)

    try:
        reading = await service.ingest(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    # Run alert checks asynchronously
    await alert_service.check_temperature(reading)

    return TelemetryResponse(
        reading_id=reading.id,
        sensor_id=reading.sensor_id,
    )


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check for webhook pipeline",
)
async def telemetry_health():
    """Simple liveness probe for the ThingsBoard webhook target URL."""
    return HealthResponse()
