"""Pydantic schemas for Sensor CRUD operations."""

from datetime import datetime

from pydantic import BaseModel, Field


class SensorCreate(BaseModel):
    device_name: str = Field(..., min_length=1, max_length=128)
    device_id: str | None = Field(None, description="ThingsBoard GUID")
    location: str | None = Field(None, max_length=256)
    is_active: bool = True


class SensorUpdate(BaseModel):
    device_name: str | None = Field(None, min_length=1, max_length=128)
    device_id: str | None = None
    location: str | None = None
    is_active: bool | None = None


class SensorOut(BaseModel):
    id: int
    device_name: str
    device_id: str | None
    location: str | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
