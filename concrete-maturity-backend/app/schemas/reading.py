"""Pydantic schemas for SensorReading queries and responses."""

from datetime import datetime

from pydantic import BaseModel


class ReadingOut(BaseModel):
    id: int
    sensor_id: int
    temperature_c: float
    maturity_c_hour: float
    simulated_hours: float
    sensor_status: bool
    data_mode: str
    recorded_at: datetime
    received_at: datetime

    model_config = {"from_attributes": True}


class ReadingPage(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[ReadingOut]
