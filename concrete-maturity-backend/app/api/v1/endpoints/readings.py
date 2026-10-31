"""Readings endpoints: paginated history and CSV export."""

import csv
import io
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.models.sensor_reading import SensorReading
from app.schemas.reading import ReadingPage

router = APIRouter()


@router.get("", response_model=ReadingPage, summary="Paginated sensor readings log")
async def list_readings(
    sensor_id: int | None = Query(None),
    data_mode: str | None = Query(None, description="Filter by 'dummy' or 'real'"),
    from_dt: datetime | None = Query(None),
    to_dt: datetime | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
) -> ReadingPage:
    base_query = select(SensorReading)
    if sensor_id is not None:
        base_query = base_query.where(SensorReading.sensor_id == sensor_id)
    if data_mode is not None:
        base_query = base_query.where(SensorReading.data_mode == data_mode)
    if from_dt is not None:
        base_query = base_query.where(SensorReading.recorded_at >= from_dt)
    if to_dt is not None:
        base_query = base_query.where(SensorReading.recorded_at <= to_dt)

    total = (await db.execute(
        select(func.count()).select_from(base_query.subquery())
    )).scalar_one()

    items_result = await db.execute(
        base_query
        .order_by(SensorReading.recorded_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = items_result.scalars().all()

    return ReadingPage(total=total, page=page, page_size=page_size, items=items)


@router.get("/export", summary="Export readings as CSV download")
async def export_readings(
    sensor_id: int | None = Query(None),
    data_mode: str | None = Query(None),
    from_dt: datetime | None = Query(None),
    to_dt: datetime | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Download matching readings as a CSV file."""
    query = select(SensorReading).order_by(SensorReading.recorded_at.asc())
    if sensor_id is not None:
        query = query.where(SensorReading.sensor_id == sensor_id)
    if data_mode is not None:
        query = query.where(SensorReading.data_mode == data_mode)
    if from_dt is not None:
        query = query.where(SensorReading.recorded_at >= from_dt)
    if to_dt is not None:
        query = query.where(SensorReading.recorded_at <= to_dt)

    result = await db.execute(query)
    readings = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "sensor_id", "temperature_c", "maturity_c_hour",
                     "simulated_hours", "sensor_status", "data_mode", "recorded_at", "received_at"])
    for r in readings:
        writer.writerow([
            r.id, r.sensor_id, r.temperature_c, r.maturity_c_hour,
            r.simulated_hours, r.sensor_status, r.data_mode, r.recorded_at, r.received_at,
        ])
    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=readings.csv"},
    )
