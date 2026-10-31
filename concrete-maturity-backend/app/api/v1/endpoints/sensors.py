"""Sensor CRUD endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.models.sensor import Sensor
from app.schemas.sensor import SensorCreate, SensorOut

router = APIRouter()


@router.get("", response_model=list[SensorOut], summary="List all registered sensors")
async def list_sensors(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Sensor).order_by(Sensor.id))
    return result.scalars().all()


@router.post(
    "",
    response_model=SensorOut,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new sensor / device",
)
async def create_sensor(payload: SensorCreate, db: AsyncSession = Depends(get_db)):
    sensor = Sensor(**payload.model_dump())
    db.add(sensor)
    await db.flush()
    await db.refresh(sensor)
    return sensor


@router.get("/{sensor_id}", response_model=SensorOut, summary="Get a sensor by ID")
async def get_sensor(sensor_id: int, db: AsyncSession = Depends(get_db)):
    sensor = await db.get(Sensor, sensor_id)
    if sensor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sensor not found.")
    return sensor
