"""Dashboard endpoints: summary, latest status, and time-series history."""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.models.alert import Alert
from app.models.sensor import Sensor
from app.models.sensor_reading import SensorReading
from app.services.maturity_service import MaturityService

router = APIRouter()


@router.get("/summary", summary="Aggregated summary metrics for the dashboard")
async def dashboard_summary(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """
    Returns:
    - Total active sensors
    - Count of critical (unresolved high-severity) alerts
    - Total readings ingested
    """
    active_sensors = (await db.execute(
        select(func.count()).select_from(Sensor).where(Sensor.is_active == True)  # noqa: E712
    )).scalar_one()

    critical_alerts = (await db.execute(
        select(func.count()).select_from(Alert).where(
            Alert.is_resolved == False, Alert.severity == "high"  # noqa: E712
        )
    )).scalar_one()

    total_readings = (await db.execute(
        select(func.count()).select_from(SensorReading)
    )).scalar_one()

    return {
        "active_sensors": active_sensors,
        "critical_alerts": critical_alerts,
        "total_readings": total_readings,
    }


@router.get("/latest", summary="Latest telemetry state across all active sensors")
async def dashboard_latest(db: AsyncSession = Depends(get_db)) -> list[dict[str, Any]]:
    """
    Returns the most recent SensorReading per active sensor, enriched with
    maturity progress percentage toward the default target.
    """
    sensors_result = await db.execute(
        select(Sensor).where(Sensor.is_active == True)  # noqa: E712
    )
    sensors = sensors_result.scalars().all()

    output = []
    for sensor in sensors:
        # Latest reading sub-query
        latest_result = await db.execute(
            select(SensorReading)
            .where(SensorReading.sensor_id == sensor.id)
            .order_by(SensorReading.received_at.desc())
            .limit(1)
        )
        reading = latest_result.scalar_one_or_none()
        if reading:
            progress = MaturityService.progress_percent(reading.maturity_c_hour)
            output.append({
                "sensor_id": sensor.id,
                "device_name": sensor.device_name,
                "location": sensor.location,
                "temperature_c": reading.temperature_c,
                "maturity_c_hour": reading.maturity_c_hour,
                "simulated_hours": reading.simulated_hours,
                "sensor_status": reading.sensor_status,
                "data_mode": reading.data_mode,
                "maturity_progress_pct": round(progress, 2),
                "received_at": reading.received_at.isoformat(),
            })
    return output


@router.get("/history", summary="Time-series temperature and maturity curves")
async def dashboard_history(
    sensor_id: int = Query(..., description="Sensor to query"),
    from_dt: datetime | None = Query(None, description="Start datetime (ISO 8601)"),
    to_dt: datetime | None = Query(None, description="End datetime (ISO 8601)"),
    limit: int = Query(500, le=2000, description="Max data points to return"),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """
    Returns time-series readings for charting temperature and maturity curves.
    Filtered by sensor_id and optional date range.
    """
    query = (
        select(SensorReading)
        .where(SensorReading.sensor_id == sensor_id)
        .order_by(SensorReading.recorded_at.asc())
        .limit(limit)
    )
    if from_dt:
        query = query.where(SensorReading.recorded_at >= from_dt)
    if to_dt:
        query = query.where(SensorReading.recorded_at <= to_dt)

    result = await db.execute(query)
    readings = result.scalars().all()

    return [
        {
            "timestamp": r.recorded_at.isoformat(),
            "temperature_c": r.temperature_c,
            "maturity_c_hour": r.maturity_c_hour,
            "simulated_hours": r.simulated_hours,
        }
        for r in readings
    ]
