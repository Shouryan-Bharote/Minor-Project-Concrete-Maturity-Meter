"""Pydantic schemas for telemetry ingestion from ThingsBoard webhook."""

from datetime import datetime

from pydantic import BaseModel, Field


class TelemetryPayload(BaseModel):
    """Matches the JSON payload forwarded by the ThingsBoard Rule Engine."""

    sensor_id: int = Field(1, description="Sensor primary key in local DB (default: 1)")
    temperature_c: float = Field(..., description="Concrete temperature in Celsius")
    maturity_c_hour: float = Field(..., description="Cumulative Nurse-Saul maturity index (°C·h)")
    simulated_hours: float = Field(..., description="Curing duration elapsed in hours")
    sensor_status: bool = Field(True, description="True if sensor is operational")
    data_mode: str = Field("real", description="'dummy' or 'real'")
    recorded_at: datetime | None = Field(None, description="ISO 8601 timestamp")
    ts: int | float | None = Field(None, description="ThingsBoard timestamp in epoch milliseconds")


class TelemetryResponse(BaseModel):
    """Response returned after successful telemetry ingestion."""

    reading_id: int
    sensor_id: int
    message: str = "Telemetry recorded successfully."


class HealthResponse(BaseModel):
    """Simple health check response for the webhook pipeline."""

    status: str = "ok"
    detail: str = "Telemetry endpoint is reachable."
