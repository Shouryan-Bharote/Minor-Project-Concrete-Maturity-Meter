"""Tests for ThingsBoard REST API service and endpoints."""

import pytest
from httpx import ASGITransport, AsyncClient, Response

from app.core.config import Settings, settings
from app.main import app
from app.services.thingsboard_service import (
    ThingsBoardAuthError,
    ThingsBoardService,
)


class MockThingsBoardTransport:
    """Mock handler simulating ThingsBoard Cloud REST APIs."""

    def __init__(self, token: str = "mock-jwt-token", device_id: str = "mock-device-uuid") -> None:
        self.token = token
        self.device_id = device_id
        self.login_attempts = 0
        self.keys_queried = False

    async def handle_request(self, request) -> Response:
        path = request.url.path
        method = request.method
        headers = request.headers

        # 1. POST /api/auth/login
        if method == "POST" and path == "/api/auth/login":
            self.login_attempts += 1
            import json
            data = json.loads(request.content.decode("utf-8"))
            if data.get("username") == "valid@tb.com" and data.get("password") == "secret123":
                return Response(200, json={"token": self.token, "refreshToken": "mock-refresh-token"})
            return Response(401, json={"message": "Invalid username or password"})

        # Check authorization header
        auth_header = headers.get("X-Authorization", "")
        if not auth_header.startswith(f"Bearer {self.token}"):
            return Response(401, json={"message": "Token expired or unauthorized"})

        # 2. GET /api/device/{device_id}
        if method == "GET" and path == f"/api/device/{self.device_id}":
            return Response(
                200,
                json={
                    "id": {"id": self.device_id, "entityType": "DEVICE"},
                    "name": "ESP32 Curing Sensor Unit 1",
                    "type": "curing_sensor",
                    "label": "Block C-2 Pile Cap",
                    "createdTime": 1730000000000,
                    "additionalInfo": {"firmware": "v1.2.0"},
                },
            )

        # 3. GET /api/plugins/telemetry/DEVICE/{device_id}/keys/timeseries
        if method == "GET" and path == f"/api/plugins/telemetry/DEVICE/{self.device_id}/keys/timeseries":
            self.keys_queried = True
            return Response(
                200,
                json=[
                    "temperature_c",
                    "maturity_c_hour",
                    "simulated_hours",
                    "sensor_status",
                    "data_mode",
                    "custom_ambient_temp",
                ],
            )

        # 4. GET /api/plugins/telemetry/DEVICE/{device_id}/values/timeseries
        if method == "GET" and path == f"/api/plugins/telemetry/DEVICE/{self.device_id}/values/timeseries":
            # Check if query parameter has startTs (historical) or not (latest)
            params = request.url.params
            if "startTs" in params:
                return Response(
                    200,
                    json={
                        "temperature_c": [
                            {"ts": 1730400000000, "value": "26.50"},
                            {"ts": 1730403600000, "value": "27.80"},
                        ],
                        "maturity_c_hour": [
                            {"ts": 1730400000000, "value": "10.25"},
                            {"ts": 1730403600000, "value": "14.03"},
                        ],
                        "simulated_hours": [
                            {"ts": 1730400000000, "value": "1.00"},
                            {"ts": 1730403600000, "value": "2.00"},
                        ],
                    },
                )
            # Latest
            return Response(
                200,
                json={
                    "temperature_c": [{"ts": 1730403600000, "value": "27.80"}],
                    "maturity_c_hour": [{"ts": 1730403600000, "value": "14.03"}],
                    "simulated_hours": [{"ts": 1730403600000, "value": "2.00"}],
                    "sensor_status": [{"ts": 1730403600000, "value": "true"}],
                    "data_mode": [{"ts": 1730403600000, "value": "real"}],
                    "custom_ambient_temp": [{"ts": 1730403600000, "value": "24.10"}],
                },
            )

        return Response(404, json={"message": f"Resource not found: {path}"})



@pytest.fixture
def mock_tb_client():
    mock_tb = MockThingsBoardTransport()

    from httpx import BaseTransport

    class DirectTransport(BaseTransport):
        def handle_request(self, req):
            raise NotImplementedError()

    from httpx import AsyncBaseTransport

    class AsyncDirectTransport(AsyncBaseTransport):
        async def handle_async_request(self, req):
            return await mock_tb.handle_request(req)

    return AsyncClient(transport=AsyncDirectTransport(), base_url="https://thingsboard.cloud")


@pytest.fixture
def tb_settings():
    return Settings(
        TB_URL="https://thingsboard.cloud",
        TB_USERNAME="valid@tb.com",
        TB_PASSWORD="secret123",
        TB_DEVICE_ID="mock-device-uuid",
    )


@pytest.mark.asyncio
async def test_tb_status_endpoint(client: AsyncClient):
    """Verifies ThingsBoard status endpoint matches current configuration state."""
    res = await client.get("/api/v1/thingsboard/status")
    assert res.status_code == 200
    body = res.json()
    assert "configured" in body
    assert body["configured"] == settings.is_tb_configured
    # Ensure sensitive credentials are never leaked in payload
    assert "tb_password" not in body
    assert "password" not in str(body).lower()


@pytest.mark.asyncio
async def test_tb_service_auth_success(tb_settings: Settings, mock_tb_client: AsyncClient):
    service = ThingsBoardService(settings=tb_settings, http_client=mock_tb_client)
    token = await service.authenticate()
    assert token == "mock-jwt-token"
    # Calling authenticate again should use cached token without additional network calls
    token_cached = await service.authenticate()
    assert token_cached == token


@pytest.mark.asyncio
async def test_tb_service_auth_failure(mock_tb_client: AsyncClient):
    bad_settings = Settings(
        TB_URL="https://thingsboard.cloud",
        TB_USERNAME="wrong@tb.com",
        TB_PASSWORD="badpassword",
        TB_DEVICE_ID="mock-device-uuid",
    )
    service = ThingsBoardService(settings=bad_settings, http_client=mock_tb_client)
    with pytest.raises(ThingsBoardAuthError):
        await service.authenticate()


@pytest.mark.asyncio
async def test_tb_service_device_info(tb_settings: Settings, mock_tb_client: AsyncClient):
    service = ThingsBoardService(settings=tb_settings, http_client=mock_tb_client)
    info = await service.get_device_info()
    assert info["id"] == "mock-device-uuid"
    assert info["name"] == "ESP32 Curing Sensor Unit 1"
    assert info["label"] == "Block C-2 Pile Cap"


@pytest.mark.asyncio
async def test_tb_service_key_discovery(tb_settings: Settings, mock_tb_client: AsyncClient):
    """Verifies that available telemetry keys are discovered automatically."""
    service = ThingsBoardService(settings=tb_settings, http_client=mock_tb_client)
    keys = await service.get_telemetry_keys()
    assert "temperature_c" in keys
    assert "maturity_c_hour" in keys
    assert "custom_ambient_temp" in keys
    assert len(keys) == 6


@pytest.mark.asyncio
async def test_tb_service_latest_telemetry(tb_settings: Settings, mock_tb_client: AsyncClient):
    """Verifies latest telemetry fetching with dynamic key discovery and value auto-mapping."""
    service = ThingsBoardService(settings=tb_settings, http_client=mock_tb_client)
    latest = await service.get_latest_telemetry()
    assert latest["device_id"] == "mock-device-uuid"
    assert latest["temperature_c"] == 27.80
    assert latest["maturity_c_hour"] == 14.03
    assert latest["simulated_hours"] == 2.00
    assert latest["sensor_status"] is True
    assert latest["data_mode"] == "real"
    # Custom keys are also preserved in raw_values
    assert latest["raw_values"]["custom_ambient_temp"] == 24.10


@pytest.mark.asyncio
async def test_tb_service_historical_telemetry(tb_settings: Settings, mock_tb_client: AsyncClient):
    """Verifies historical telemetry timeseries aggregation and chronological order."""
    service = ThingsBoardService(settings=tb_settings, http_client=mock_tb_client)
    hist = await service.get_historical_telemetry()
    assert hist["count"] == 2
    pts = hist["data"]
    assert pts[0]["temperature_c"] == 26.50
    assert pts[1]["temperature_c"] == 27.80
    assert pts[0]["ts"] < pts[1]["ts"]


@pytest.mark.asyncio
async def test_tb_endpoint_dependency_override(tb_settings: Settings, mock_tb_client: AsyncClient):
    """Test API endpoint /api/v1/thingsboard/telemetry/latest with dependency injection."""
    from app.api.v1.endpoints.thingsboard import get_tb_service

    test_service = ThingsBoardService(settings=tb_settings, http_client=mock_tb_client)
    app.dependency_overrides[get_tb_service] = lambda: test_service

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            resp = await c.get("/api/v1/thingsboard/telemetry/latest")
            assert resp.status_code == 200
            data = resp.json()
            assert data["temperature_c"] == 27.80
            assert "maturity_c_hour" in data

            # Test keys endpoint
            keys_resp = await c.get("/api/v1/thingsboard/keys")
            assert keys_resp.status_code == 200
            assert "custom_ambient_temp" in keys_resp.json()["keys"]

            # Test device endpoint
            dev_resp = await c.get("/api/v1/thingsboard/device")
            assert dev_resp.status_code == 200
            assert dev_resp.json()["name"] == "ESP32 Curing Sensor Unit 1"
    finally:
        app.dependency_overrides.clear()
