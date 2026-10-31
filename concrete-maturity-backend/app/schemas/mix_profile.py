"""Pydantic schemas for MixProfile CRUD."""

from datetime import datetime

from pydantic import BaseModel, Field


class MixProfileCreate(BaseModel):
    mix_name: str = Field(..., min_length=1, max_length=256, description="e.g. C30/37 Rapid Hardening")
    datum_temperature: float = Field(-10.0, description="Nurse-Saul datum temperature (°C)")
    target_maturity: float = Field(..., gt=0, description="Target maturity (°C·h) required before stripping forms")


class MixProfileOut(BaseModel):
    id: int
    mix_name: str
    datum_temperature: float
    target_maturity: float
    created_at: datetime

    model_config = {"from_attributes": True}
