"""Integration tests for the dashboard endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_dashboard_summary(client: AsyncClient):
    response = await client.get("/api/v1/dashboard/summary")
    assert response.status_code == 200
    body = response.json()
    assert "active_sensors" in body
    assert "critical_alerts" in body
    assert "total_readings" in body


@pytest.mark.asyncio
async def test_dashboard_latest(client: AsyncClient):
    response = await client.get("/api/v1/dashboard/latest")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_dashboard_history(client: AsyncClient):
    response = await client.get("/api/v1/dashboard/history?sensor_id=1")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_mix_profiles_crud(client: AsyncClient):
    # Create profile
    payload = {
        "mix_name": "C30/37 Rapid Hardening",
        "datum_temperature": -10.0,
        "target_maturity": 480.0,
    }
    response = await client.post("/api/v1/mix-profiles", json=payload)
    assert response.status_code == 201
    profile = response.json()
    assert profile["mix_name"] == "C30/37 Rapid Hardening"
    profile_id = profile["id"]

    # List profiles
    list_res = await client.get("/api/v1/mix-profiles")
    assert list_res.status_code == 200
    assert any(p["id"] == profile_id for p in list_res.json())

    # Delete profile
    del_res = await client.delete(f"/api/v1/mix-profiles/{profile_id}")
    assert del_res.status_code == 204


@pytest.mark.asyncio
async def test_direct_latest_and_dashboard(client: AsyncClient):
    # Test compatibility endpoint for Concrete-Maturity-Meter frontend
    res = await client.get("/api/latest")
    assert res.status_code == 200
    data = res.json()
    assert "temperature_c" in data

    # Test dashboard static page mount
    dash_res = await client.get("/dashboard")
    assert dash_res.status_code in (200, 307)
