"""Integration tests for the telemetry ingestion endpoint."""

import pytest
from httpx import AsyncClient

from app.core.config import settings

HEADERS = {"X-API-Key": settings.WEBHOOK_API_KEY, "Content-Type": "application/json"}


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/api/v1/telemetry/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_ingest_telemetry_success(client: AsyncClient):
    payload = {
        "sensor_id": 1,
        "temperature_c": 28.5,
        "maturity_c_hour": 6.417,
        "simulated_hours": 0.167,
        "sensor_status": True,
        "data_mode": "dummy",
    }
    response = await client.post("/api/v1/telemetry", json=payload, headers=HEADERS)
    assert response.status_code == 201
    body = response.json()
    assert body["sensor_id"] == 1
    assert "reading_id" in body


@pytest.mark.asyncio
async def test_ingest_telemetry_unauthorized(client: AsyncClient):
    payload = {
        "sensor_id": 1,
        "temperature_c": 25.0,
        "maturity_c_hour": 5.0,
        "simulated_hours": 0.1,
        "sensor_status": True,
        "data_mode": "real",
    }
    response = await client.post("/api/v1/telemetry", json=payload)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_ingest_telemetry_with_thingsboard_ts(client: AsyncClient):
    payload = {
        "sensor_id": 1,
        "temperature_c": 29.0,
        "maturity_c_hour": 12.5,
        "simulated_hours": 0.5,
        "ts": 1730400000000,
    }
    response = await client.post("/api/v1/telemetry", json=payload, headers=HEADERS)
    assert response.status_code == 201
    body = response.json()
    assert body["sensor_id"] == 1
    assert "reading_id" in body
