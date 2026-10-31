"""Pydantic schemas for Alert queries and resolution."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class AlertOut(BaseModel):
    id: int
    sensor_id: int
    alert_type: str
    message: str
    severity: Literal["low", "medium", "high"]
    is_resolved: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AlertResolve(BaseModel):
    is_resolved: bool = Field(..., description="Set to true to acknowledge/resolve the alert.")
