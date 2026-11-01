"""Pydantic schemas for ThingsBoard REST API integration."""

from typing import Any

from pydantic import BaseModel, Field


class ThingsBoardStatusResponse(BaseModel):
    """Status of ThingsBoard configuration."""

    configured: bool = Field(..., description="True if TB credentials and device ID are set in .env")
    tb_url: str | None = Field(None, description="ThingsBoard instance URL")
    device_id: str | None = Field(None, description="Configured ThingsBoard device GUID")
    message: str = Field(..., description="Human-readable status summary")


class ThingsBoardDeviceInfo(BaseModel):
    """Device metadata returned by ThingsBoard REST API."""

    id: str = Field(..., description="Device GUID/UUID")
    name: str = Field(..., description="Device name in ThingsBoard")
    type: str | None = Field(None, description="Device profile/type")
    label: str | None = Field(None, description="Device label")
    created_time: int | None = Field(None, description="Creation timestamp in epoch ms")
    additional_info: dict[str, Any] | None = Field(default_factory=dict, description="Metadata dictionary")


class ThingsBoardDiscoveredKeys(BaseModel):
    """Available timeseries telemetry keys discovered from the device."""

    device_id: str
    keys: list[str] = Field(default_factory=list, description="List of discovered telemetry keys")
    count: int = Field(..., description="Total number of discovered keys")


class ThingsBoardTelemetryLatest(BaseModel):
    """Latest telemetry reading from ThingsBoard with auto-mapped maturity metrics."""

    device_id: str
    keys: list[str] = Field(default_factory=list, description="Discovered keys present in telemetry")
    raw_values: dict[str, Any] = Field(default_factory=dict, description="All discovered keys and their latest values")
    temperature_c: float | None = Field(None, description="Auto-mapped temperature in °C")
    maturity_c_hour: float | None = Field(None, description="Auto-mapped Nurse-Saul maturity index")
    simulated_hours: float | None = Field(None, description="Auto-mapped curing duration in hours")
    sensor_status: bool | None = Field(None, description="Auto-mapped sensor status flag")
    data_mode: str | None = Field(None, description="Auto-mapped data mode ('real' or 'dummy')")
    ts: int | None = Field(None, description="Latest timestamp in epoch ms")
    recorded_at: str | None = Field(None, description="ISO 8601 formatted timestamp")


class ThingsBoardHistoryPoint(BaseModel):
    """Single time-series point for historical charts."""

    ts: int = Field(..., description="Timestamp in epoch ms")
    recorded_at: str = Field(..., description="ISO 8601 timestamp")
    values: dict[str, Any] = Field(default_factory=dict, description="Values for all queried keys at this timestamp")
    temperature_c: float | None = Field(None, description="Temperature in °C if present")
    maturity_c_hour: float | None = Field(None, description="Maturity if present")
    simulated_hours: float | None = Field(None, description="Elapsed hours if present")


class ThingsBoardHistoryResponse(BaseModel):
    """Historical telemetry response for charting."""

    device_id: str
    keys: list[str] = Field(default_factory=list, description="Keys included in history")
    count: int = Field(..., description="Total points returned")
    data: list[ThingsBoardHistoryPoint] = Field(default_factory=list, description="Chronological time-series points")
