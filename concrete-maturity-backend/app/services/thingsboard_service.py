"""ThingsBoard REST API client service.

Handles:
- JWT authentication against ThingsBoard REST API (/api/auth/login)
- Device information retrieval (/api/device/{deviceId})
- Dynamic telemetry keys discovery (/api/plugins/telemetry/DEVICE/{deviceId}/keys/timeseries)
- Latest timeseries telemetry retrieval (/api/plugins/telemetry/DEVICE/{deviceId}/values/timeseries)
- Historical telemetry retrieval with timeseries aggregation
- Resilient token caching and automatic re-authentication on 401
"""

from datetime import UTC, datetime
from typing import Any

import httpx

from app.core.config import Settings, get_settings


class ThingsBoardError(Exception):
    """Base exception for ThingsBoard integration errors."""

    def __init__(self, message: str, status_code: int = 502) -> None:
        super().__init__(message)
        self.status_code = status_code


class ThingsBoardConfigError(ThingsBoardError):
    """Raised when required ThingsBoard configuration is missing in .env."""

    def __init__(self, message: str = "ThingsBoard credentials are not configured in .env.") -> None:
        super().__init__(message, status_code=400)


class ThingsBoardAuthError(ThingsBoardError):
    """Raised when authentication against ThingsBoard fails."""

    def __init__(self, message: str = "Failed to authenticate with ThingsBoard.") -> None:
        super().__init__(message, status_code=401)


class ThingsBoardNotFoundError(ThingsBoardError):
    """Raised when a device or entity is not found in ThingsBoard."""

    def __init__(self, message: str = "Device not found in ThingsBoard.") -> None:
        super().__init__(message, status_code=404)


class ThingsBoardConnectionError(ThingsBoardError):
    """Raised when connecting to ThingsBoard server fails."""

    def __init__(self, message: str = "Cannot connect to ThingsBoard server.") -> None:
        super().__init__(message, status_code=502)


def _parse_raw_value(val: Any) -> Any:
    """Convert raw string values from ThingsBoard timeseries to native types."""
    if val is None:
        return None
    if isinstance(val, (int, float, bool)):
        return val
    val_str = str(val).strip()
    if val_str.lower() == "true":
        return True
    if val_str.lower() == "false":
        return False
    try:
        if "." in val_str:
            return float(val_str)
        return int(val_str)
    except ValueError:
        return val_str


class ThingsBoardService:
    """Async service to interact with ThingsBoard via official REST APIs."""

    def __init__(self, settings: Settings | None = None, http_client: httpx.AsyncClient | None = None) -> None:
        self.settings = settings or get_settings()
        self._custom_client = http_client
        self._token: str | None = None
        self._token_fetched_at: datetime | None = None

    @property
    def base_url(self) -> str:
        return self.settings.TB_URL.strip().rstrip("/")

    @property
    def device_id(self) -> str:
        return self.settings.TB_DEVICE_ID.strip()

    def _ensure_configured(self) -> None:
        """Validate that all required credentials are present."""
        missing = []
        if not self.settings.TB_URL.strip():
            missing.append("TB_URL")
        if not self.settings.TB_USERNAME.strip():
            missing.append("TB_USERNAME")
        if not self.settings.TB_PASSWORD.strip():
            missing.append("TB_PASSWORD")
        if not self.settings.TB_DEVICE_ID.strip():
            missing.append("TB_DEVICE_ID")

        if missing:
            raise ThingsBoardConfigError(
                f"Missing ThingsBoard environment variables: {', '.join(missing)}. "
                "Please configure them in your .env file."
            )

    async def _get_client(self) -> httpx.AsyncClient:
        if self._custom_client is not None:
            return self._custom_client
        return httpx.AsyncClient(timeout=10.0)

    async def authenticate(self, force_refresh: bool = False) -> str:
        """
        Authenticate against ThingsBoard via POST /api/auth/login.
        Returns the JWT access token and caches it.
        """
        self._ensure_configured()

        if self._token and not force_refresh:
            return self._token

        login_url = f"{self.base_url}/api/auth/login"
        payload = {
            "username": self.settings.TB_USERNAME,
            "password": self.settings.TB_PASSWORD,
        }

        client = await self._get_client()
        should_close = self._custom_client is None

        try:
            resp = await client.post(
                login_url,
                json=payload,
                headers={"Accept": "application/json", "Content-Type": "application/json"},
            )
            if resp.status_code == 401:
                raise ThingsBoardAuthError("Invalid ThingsBoard username or password.")
            resp.raise_for_status()

            data = resp.json()
            token = data.get("token")
            if not token:
                raise ThingsBoardAuthError("Authentication succeeded but no token was returned by ThingsBoard.")

            self._token = token
            self._token_fetched_at = datetime.now(UTC)
            return self._token
        except httpx.ConnectError as exc:
            raise ThingsBoardConnectionError(f"Cannot reach ThingsBoard at {self.base_url}: {exc}") from exc
        except httpx.TimeoutException as exc:
            raise ThingsBoardConnectionError(f"Connection to ThingsBoard timed out: {exc}") from exc
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 401:
                raise ThingsBoardAuthError("Invalid ThingsBoard username or password.") from exc
            raise ThingsBoardError(
                f"ThingsBoard login failed with HTTP {exc.response.status_code}: {exc.response.text}",
                status_code=exc.response.status_code,
            ) from exc
        finally:
            if should_close:
                await client.aclose()

    async def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json_data: Any = None,
        retried: bool = False,
    ) -> Any:
        """Execute an authenticated request against ThingsBoard with auto token retry."""
        token = await self.authenticate()
        url = f"{self.base_url}{path}"
        headers = {
            "X-Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

        client = await self._get_client()
        should_close = self._custom_client is None

        try:
            resp = await client.request(
                method,
                url,
                params=params,
                json=json_data,
                headers=headers,
            )

            # Auto re-authenticate on token expiration (401)
            if resp.status_code == 401 and not retried:
                self._token = None
                await self.authenticate(force_refresh=True)
                return await self._request(
                    method, path, params=params, json_data=json_data, retried=True
                )

            if resp.status_code == 404:
                raise ThingsBoardNotFoundError(f"Requested resource not found at {path}")

            resp.raise_for_status()
            if resp.content:
                return resp.json()
            return None
        except httpx.ConnectError as exc:
            raise ThingsBoardConnectionError(f"Cannot reach ThingsBoard at {self.base_url}: {exc}") from exc
        except httpx.TimeoutException as exc:
            raise ThingsBoardConnectionError(f"Request to ThingsBoard timed out: {exc}") from exc
        except httpx.HTTPStatusError as exc:
            raise ThingsBoardError(
                f"ThingsBoard request failed ({exc.response.status_code}): {exc.response.text}",
                status_code=exc.response.status_code,
            ) from exc
        finally:
            if should_close:
                await client.aclose()

    async def get_device_info(self) -> dict[str, Any]:
        """Fetch device information from ThingsBoard (/api/device/{deviceId})."""
        self._ensure_configured()
        data = await self._request("GET", f"/api/device/{self.device_id}")

        device_uuid = data.get("id", {}).get("id", self.device_id) if isinstance(data.get("id"), dict) else self.device_id
        return {
            "id": device_uuid,
            "name": data.get("name", "Unknown Device"),
            "type": data.get("type"),
            "label": data.get("label"),
            "created_time": data.get("createdTime"),
            "additional_info": data.get("additionalInfo") or {},
        }

    async def get_telemetry_keys(self) -> list[str]:
        """
        Dynamically discover available timeseries telemetry keys for the device.
        Calls /api/plugins/telemetry/DEVICE/{deviceId}/keys/timeseries.
        """
        self._ensure_configured()
        path = f"/api/plugins/telemetry/DEVICE/{self.device_id}/keys/timeseries"
        keys = await self._request("GET", path)
        if isinstance(keys, list):
            return [str(k) for k in keys]
        return []

    @staticmethod
    def _find_key_match(keys: list[str], candidates: list[str], substring: str | None = None) -> str | None:
        """Find a telemetry key by candidate exact match (case-insensitive) or substring."""
        lower_keys = {k.lower(): k for k in keys}
        for cand in candidates:
            if cand.lower() in lower_keys:
                return lower_keys[cand.lower()]
        if substring:
            for k in keys:
                if substring.lower() in k.lower():
                    return k
        return None

    async def get_latest_telemetry(self) -> dict[str, Any]:
        """
        Fetch latest telemetry for the device by dynamically discovering available keys.
        Auto-maps concrete maturity metrics (temperature, maturity, hours, status, data_mode).
        """
        self._ensure_configured()

        # Step 1: Automatically discover available telemetry keys
        discovered_keys = await self.get_telemetry_keys()
        if not discovered_keys:
            return {
                "device_id": self.device_id,
                "keys": [],
                "raw_values": {},
                "temperature_c": None,
                "maturity_c_hour": None,
                "simulated_hours": None,
                "sensor_status": None,
                "data_mode": None,
                "ts": None,
                "recorded_at": None,
            }

        # Step 2: Fetch latest timeseries values for all discovered keys
        keys_param = ",".join(discovered_keys)
        path = f"/api/plugins/telemetry/DEVICE/{self.device_id}/values/timeseries"
        raw_res = await self._request("GET", path, params={"keys": keys_param})

        raw_values: dict[str, Any] = {}
        max_ts: int | None = None

        if isinstance(raw_res, dict):
            for key, entries in raw_res.items():
                if isinstance(entries, list) and len(entries) > 0:
                    latest_entry = entries[0]
                    ts = latest_entry.get("ts")
                    val = _parse_raw_value(latest_entry.get("value"))
                    raw_values[key] = val
                    if ts is not None and (max_ts is None or ts > max_ts):
                        max_ts = ts

        # Step 3: Dynamic auto-mapping for concrete maturity domain fields
        temp_key = self._find_key_match(
            discovered_keys,
            ["temperature_c", "temperature", "temp", "temp_c"],
            substring="temp",
        )
        mat_key = self._find_key_match(
            discovered_keys,
            ["maturity_c_hour", "maturity_c_h", "maturity", "mat"],
            substring="matur",
        )
        hours_key = self._find_key_match(
            discovered_keys,
            ["simulated_hours", "elapsed_hours", "curing_hours", "hours"],
            substring="hour",
        )
        status_key = self._find_key_match(
            discovered_keys,
            ["sensor_status", "status", "connected", "online"],
            substring="status",
        )
        mode_key = self._find_key_match(
            discovered_keys,
            ["data_mode", "mode"],
            substring="mode",
        )

        temp_val = raw_values.get(temp_key) if temp_key else None
        mat_val = raw_values.get(mat_key) if mat_key else None
        hours_val = raw_values.get(hours_key) if hours_key else None
        status_val = raw_values.get(status_key) if status_key else None
        mode_val = raw_values.get(mode_key) if mode_key else None

        recorded_at_iso = None
        if max_ts is not None:
            ts_sec = max_ts / 1000.0 if max_ts > 1e11 else float(max_ts)
            recorded_at_iso = datetime.fromtimestamp(ts_sec, tz=UTC).isoformat()

        return {
            "device_id": self.device_id,
            "keys": discovered_keys,
            "raw_values": raw_values,
            "temperature_c": float(temp_val) if isinstance(temp_val, (int, float)) else None,
            "maturity_c_hour": float(mat_val) if isinstance(mat_val, (int, float)) else None,
            "simulated_hours": float(hours_val) if isinstance(hours_val, (int, float)) else None,
            "sensor_status": bool(status_val) if status_val is not None else True,
            "data_mode": str(mode_val) if mode_val is not None else "real",
            "ts": max_ts,
            "recorded_at": recorded_at_iso,
        }

    async def get_historical_telemetry(
        self,
        start_ts: int | None = None,
        end_ts: int | None = None,
        limit: int = 500,
        keys: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Fetch historical time-series telemetry from ThingsBoard.
        If keys is None, automatically discovers available keys.
        Returns points ordered chronologically.
        """
        self._ensure_configured()

        # Step 1: Discover keys if not supplied
        active_keys = keys or await self.get_telemetry_keys()
        if not active_keys:
            return {"device_id": self.device_id, "keys": [], "count": 0, "data": []}

        # Default time window: last 7 days to now
        now_ms = int(datetime.now(UTC).timestamp() * 1000)
        end_ts = end_ts or now_ms
        start_ts = start_ts or (end_ts - (7 * 24 * 3600 * 1000))

        params = {
            "keys": ",".join(active_keys),
            "startTs": start_ts,
            "endTs": end_ts,
            "limit": limit,
            "orderBy": "ASC",
        }

        path = f"/api/plugins/telemetry/DEVICE/{self.device_id}/values/timeseries"
        res = await self._request("GET", path, params=params)

        # Merge timeseries points across keys grouped by timestamp
        temp_key = self._find_key_match(active_keys, ["temperature_c", "temperature", "temp"], substring="temp")
        mat_key = self._find_key_match(active_keys, ["maturity_c_hour", "maturity", "mat"], substring="matur")
        hours_key = self._find_key_match(active_keys, ["simulated_hours", "hours"], substring="hour")

        points_by_ts: dict[int, dict[str, Any]] = {}

        if isinstance(res, dict):
            for k, entries in res.items():
                if isinstance(entries, list):
                    for entry in entries:
                        ts = entry.get("ts")
                        if ts is None:
                            continue
                        val = _parse_raw_value(entry.get("value"))
                        if ts not in points_by_ts:
                            points_by_ts[ts] = {}
                        points_by_ts[ts][k] = val

        sorted_ts = sorted(points_by_ts.keys())
        data_points = []
        for ts in sorted_ts:
            vals = points_by_ts[ts]
            ts_sec = ts / 1000.0 if ts > 1e11 else float(ts)
            iso_str = datetime.fromtimestamp(ts_sec, tz=UTC).isoformat()

            tv = vals.get(temp_key) if temp_key else None
            mv = vals.get(mat_key) if mat_key else None
            hv = vals.get(hours_key) if hours_key else None

            data_points.append({
                "ts": ts,
                "recorded_at": iso_str,
                "values": vals,
                "temperature_c": float(tv) if isinstance(tv, (int, float)) else None,
                "maturity_c_hour": float(mv) if isinstance(mv, (int, float)) else None,
                "simulated_hours": float(hv) if isinstance(hv, (int, float)) else None,
            })

        return {
            "device_id": self.device_id,
            "keys": active_keys,
            "count": len(data_points),
            "data": data_points,
        }
