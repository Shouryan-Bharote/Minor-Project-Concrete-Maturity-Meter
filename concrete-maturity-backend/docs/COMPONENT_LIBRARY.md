# Component Library

This document outlines key components, abstractions, and algorithms across the backend.

## 1. Nurse-Saul Maturity Calculation (`app/services/maturity_service.py`)
Maturity index $M$ computes accumulated curing exposure over time:

$$M = \sum (T_a - T_0) \Delta t$$

- $T_a$: Concrete temperature in °C
- $T_0$: Datum temperature (default: `-10.0°C`)
- $\Delta t$: Time increment in hours

The `MaturityService.progress_percent` method compares cumulative maturity against mix target thresholds (e.g. 500 °C·h) to determine formwork stripping readiness.

## 2. Ingestion Pipeline (`app/services/telemetry_service.py`)
- Validates the incoming payload against `TelemetryPayload`.
- Checks for an existing sensor; if `sensor_id == 1` and not found, auto-provisions a bootstrap sensor.
- Persists data to `sensor_readings`.
- Triggers alert inspection via `AlertService`.

## 3. Alert Evaluator (`app/services/alert_service.py`)
- **Temperature Thresholds**: Alerts on extremes ($T > 70^\circ\text{C}$ or $T < -5^\circ\text{C}$).
- **Heartbeat Disconnect**: Detects when active sensors fail to transmit within a configurable window (default 5 minutes).

## 4. REST Endpoints Matrix
| Method | Route | Description | Auth |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/telemetry` | Webhook ingestion from ThingsBoard | `X-API-Key` |
| `GET` | `/api/v1/telemetry/health` | Webhook liveness probe | None |
| `GET` | `/api/v1/sensors` | List registered sensors | None |
| `POST` | `/api/v1/sensors` | Register new sensor | None |
| `GET` | `/api/v1/dashboard/summary` | Active sensors, total readings, critical alerts | None |
| `GET` | `/api/v1/dashboard/latest` | Latest reading & maturity % per sensor | None |
| `GET` | `/api/v1/dashboard/history` | Time-series data for charting | None |
| `GET` | `/api/v1/readings` | Paginated readings log | None |
| `GET` | `/api/v1/readings/export` | CSV export download | None |
| `GET` | `/api/v1/alerts` | Active unresolved alerts | None |
| `PATCH` | `/api/v1/alerts/{id}` | Resolve alert | None |
