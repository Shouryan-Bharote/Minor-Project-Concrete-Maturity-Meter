"""ThingsBoard REST API endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.database.connection import get_db
from app.schemas.telemetry import TelemetryPayload
from app.schemas.thingsboard import (
    ThingsBoardDeviceInfo,
    ThingsBoardDiscoveredKeys,
    ThingsBoardHistoryResponse,
    ThingsBoardStatusResponse,
    ThingsBoardTelemetryLatest,
)
from app.services.alert_service import AlertService
from app.services.telemetry_service import TelemetryService
from app.services.thingsboard_service import (
    ThingsBoardAuthError,
    ThingsBoardConfigError,
    ThingsBoardConnectionError,
    ThingsBoardError,
    ThingsBoardNotFoundError,
    ThingsBoardService,
)

router = APIRouter()


def get_tb_service() -> ThingsBoardService:
    """Dependency provider for ThingsBoardService."""
    return ThingsBoardService(settings)


@router.get(
    "/status",
    response_model=ThingsBoardStatusResponse,
    summary="ThingsBoard integration status",
)
async def get_status(service: ThingsBoardService = Depends(get_tb_service)):
    """
    Check if ThingsBoard integration is configured in environment variables.
    Credentials and passwords are never exposed.
    """
    is_conf = settings.is_tb_configured
    if not is_conf:
        return ThingsBoardStatusResponse(
            configured=False,
            tb_url=settings.TB_URL if settings.TB_URL else None,
            device_id=settings.TB_DEVICE_ID if settings.TB_DEVICE_ID else None,
            message="ThingsBoard integration is not configured. Please supply required TB credentials in .env.",
        )

    return ThingsBoardStatusResponse(
        configured=True,
        tb_url=service.base_url,
        device_id=service.device_id,
        message="ThingsBoard configuration is active.",
    )


@router.get(
    "/device",
    response_model=ThingsBoardDeviceInfo,
    summary="Fetch device information from ThingsBoard",
)
async def get_device_info(service: ThingsBoardService = Depends(get_tb_service)):
    """Fetch device metadata and label from ThingsBoard REST API."""
    try:
        return await service.get_device_info()
    except ThingsBoardConfigError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except ThingsBoardAuthError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except ThingsBoardNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ThingsBoardConnectionError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    except ThingsBoardError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.get(
    "/keys",
    response_model=ThingsBoardDiscoveredKeys,
    summary="Automatically discover available telemetry keys",
)
async def discover_telemetry_keys(service: ThingsBoardService = Depends(get_tb_service)):
    """
    Query ThingsBoard to discover all telemetry keys registered for the device,
    without making any assumptions about key names.
    """
    try:
        keys = await service.get_telemetry_keys()
        return ThingsBoardDiscoveredKeys(
            device_id=service.device_id,
            keys=keys,
            count=len(keys),
        )
    except ThingsBoardConfigError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except ThingsBoardAuthError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except ThingsBoardConnectionError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    except ThingsBoardError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.get(
    "/telemetry/latest",
    response_model=ThingsBoardTelemetryLatest,
    summary="Fetch latest telemetry with discovered keys",
)
async def get_latest_telemetry(service: ThingsBoardService = Depends(get_tb_service)):
    """
    Dynamically discovers all telemetry keys and fetches the most recent
    values from ThingsBoard. Automatically maps concrete temperature, maturity,
    and curing duration if present.
    """
    try:
        return await service.get_latest_telemetry()
    except ThingsBoardConfigError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except ThingsBoardAuthError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except ThingsBoardConnectionError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    except ThingsBoardError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.get(
    "/telemetry/history",
    response_model=ThingsBoardHistoryResponse,
    summary="Fetch historical telemetry for charting",
)
async def get_historical_telemetry(
    start_ts: int | None = Query(None, description="Start timestamp in epoch ms"),
    end_ts: int | None = Query(None, description="End timestamp in epoch ms"),
    limit: int = Query(500, le=5000, description="Max points per key"),
    keys: str | None = Query(None, description="Comma-separated keys (optional; auto-discovered if omitted)"),
    service: ThingsBoardService = Depends(get_tb_service),
):
    """
    Fetch historical time-series data for the device. Automatically discovers
    keys if not explicitly specified.
    """
    try:
        active_keys = [k.strip() for k in keys.split(",") if k.strip()] if keys else None
        data = await service.get_historical_telemetry(
            start_ts=start_ts,
            end_ts=end_ts,
            limit=limit,
            keys=active_keys,
        )
        return data
    except ThingsBoardConfigError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except ThingsBoardAuthError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except ThingsBoardConnectionError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    except ThingsBoardError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.post(
    "/sync",
    summary="Fetch latest ThingsBoard telemetry and sync into database",
)
async def sync_latest_to_db(
    service: ThingsBoardService = Depends(get_tb_service),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Pulls the latest reading from ThingsBoard and persists it into the local database
    as a SensorReading, running alert threshold checks.
    """
    try:
        latest = await service.get_latest_telemetry()
    except ThingsBoardConfigError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except ThingsBoardAuthError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except ThingsBoardConnectionError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    except ThingsBoardError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

    if latest.get("temperature_c") is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No valid temperature reading found in latest ThingsBoard telemetry to sync.",
        )

    payload = TelemetryPayload(
        sensor_id=1,
        temperature_c=latest["temperature_c"],
        maturity_c_hour=latest["maturity_c_hour"] if latest["maturity_c_hour"] is not None else 0.0,
        simulated_hours=latest["simulated_hours"] if latest["simulated_hours"] is not None else 0.0,
        sensor_status=latest["sensor_status"] if latest["sensor_status"] is not None else True,
        data_mode=latest["data_mode"] if latest["data_mode"] is not None else "real",
        ts=latest.get("ts"),
    )

    t_service = TelemetryService(db)
    alert_service = AlertService(db)
    reading = await t_service.ingest(payload)
    await alert_service.check_temperature(reading)

    return {
        "status": "synced",
        "reading_id": reading.id,
        "temperature_c": reading.temperature_c,
        "maturity_c_hour": reading.maturity_c_hour,
        "recorded_at": reading.recorded_at.isoformat(),
    }
