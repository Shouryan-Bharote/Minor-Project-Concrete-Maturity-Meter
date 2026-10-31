# System Blueprint: ESP32 Concrete Maturity Meter & FastAPI Integration

## 1. Executive Summary & Architecture Overview

The system monitors concrete curing in real time using the **Nurse-Saul maturity method**. It implements a 5-tier architecture connecting field sensors to an end-user dashboard:

```
[DS18B20 Temp Sensor]
        │ 1-Wire (GPIO 27, 4.7kΩ pull-up)
        ▼
[ESP32-S3 Microcontroller] ──(I2C: GPIO 20/21)──► [OLED SSD1306 Display]
        │
        │ Wi-Fi (WPA2) + MQTT (Port 1883 / TLS 8883)
        │ Topic: v1/devices/me/telemetry
        ▼
[ThingsBoard Cloud IoT Platform]
        │
        │ Rule Engine (REST API Call Node / HTTP POST Webhook)
        │ *Requires Public HTTPS Tunnel during local dev*
        ▼
[FastAPI Backend Server] (Python 3.12, Uvicorn, Pydantic)
        │
        │ SQLAlchemy 2.0 ORM
        ▼
[SQLite Database] (Sensor, SensorReading, Alert, MixProfile)
        │
        │ REST API (JSON)
        ▼
[Frontend Web Dashboard] (Live Status, Time-Series Charts, Mix Analysis)
```

---

## 2. Hardware Layer & Pin Configuration

| Component | Interface / Pin | Description / Notes |
| :--- | :--- | :--- |
| **Microcontroller** | ESP32-S3 | Core processing, maturity math, Wi-Fi & MQTT |
| **Temperature Sensor** | DS18B20 on **GPIO 27** | 1-Wire protocol, requires 4.7 kΩ pull-up to 3.3V |
| **OLED Display** | SSD1306 (128×64) | I2C address `0x3C` |
| | **SDA: GPIO 21** | I2C Data line |
| | **SCL: GPIO 20** | I2C Clock line |

### Nurse-Saul Maturity Computation
The concrete maturity index $M$ is accumulated over time based on measured temperature:
$$M = \sum (T_a - T_0) \Delta t$$
- **$T_a$**: Concrete temperature (°C)
- **$T_0$**: Datum temperature (set to **`-10.0°C`**)
- **$\Delta t$**: Time interval in hours

### Sampling & Simulation Modes
- **Sampling Interval**: Sampled every **10,000 ms (10 seconds)**.
- **`DEMO_MODE true`**: 1 real second = 1 simulated minute (60 real seconds = 1 simulated hour).
- **`DEMO_MODE false`**: Real-time curing measurement ($\Delta t = \text{seconds} / 3600$).
- **`USE_DUMMY_DATA true`**: Toggles dummy simulated data generation without requiring a physical probe.

---

## 3. Communication Protocols & Telemetry Contracts

### A. ESP32 to ThingsBoard Cloud (MQTT)
- **Host**: `mqtt.thingsboard.cloud`
- **Port**: `1883` (Testing) / `8883` (Production TLS)
- **Topic**: `v1/devices/me/telemetry`
- **Client ID**: `ESP32_Concrete_Maturity`
- **Username**: Device Access Token (e.g., `concrete`)
- **Password**: Empty string

**JSON Payload Schema:**
```json
{
  "sensor_id": 1,
  "temperature_c": 28.50,
  "maturity_c_hour": 6.417,
  "simulated_hours": 0.167,
  "sensor_status": true,
  "data_mode": "dummy"
}
```

### B. ThingsBoard to FastAPI (Rule Engine Webhook)
- **Node**: Rule Engine **REST API Call Node**
- **Method**: `POST`
- **Headers**: `Content-Type: application/json`
- **Target URL**: `https://<public-tunnel-or-domain>/api/v1/telemetry`
- **Payload**: Forwards incoming device telemetry with server timestamps.

---

## 4. FastAPI Backend Architecture

Managed with **uv** and running **Python 3.12**:

```
concrete-maturity-backend/
├── app/
│   ├── main.py                  # FastAPI application entry & middleware
│   ├── core/
│   │   ├── config.py            # Pydantic BaseSettings (.env loader)
│   │   └── security.py          # Webhook API keys / auth tokens
│   ├── database/
│   │   ├── connection.py        # SQLAlchemy engine & session factory
│   │   └── base.py              # Declarative Base
│   ├── models/                  # SQLAlchemy ORM models
│   │   ├── sensor.py
│   │   ├── sensor_reading.py
│   │   ├── alert.py
│   │   └── mix_profile.py
│   ├── schemas/                 # Pydantic schemas (in/out validation)
│   │   ├── telemetry.py
│   │   ├── sensor.py
│   │   ├── reading.py
│   │   └── alert.py
│   ├── api/
│   │   └── v1/
│   │       ├── router.py        # Central v1 APIRouter aggregator
│   │       └── endpoints/
│   │           ├── telemetry.py # Ingestion endpoint (/api/v1/telemetry)
│   │           ├── sensors.py   # CRUD for sensors
│   │           ├── dashboard.py # Aggregated UI stats
│   │           ├── readings.py  # Historical queries & exports
│   │           └── alerts.py    # Alert resolution
│   ├── services/                # Business logic
│   │   ├── telemetry_service.py # Ingestion & duplicate detection
│   │   ├── maturity_service.py  # Target progress calculation
│   │   └── alert_service.py     # Threshold checks & sensor disconnects
│   └── utils/
│       └── datetime.py
├── tests/
│   ├── test_telemetry.py
│   └── test_dashboard.py
├── .env.example
├── pyproject.toml
└── uv.lock
```

---

## 5. Database Schema (SQLite / SQLAlchemy)

### Tables Specification

#### 1. `Sensor`
- `id` (Integer, Primary Key)
- `device_name` (String, e.g. "Concrete Sensor 01")
- `device_id` (String, ThingsBoard GUID)
- `location` (String, e.g. "Pour Zone B")
- `is_active` (Boolean, default True)
- `created_at` (DateTime, default UTC now)

#### 2. `SensorReading`
- `id` (Integer, Primary Key)
- `sensor_id` (Integer, Foreign Key -> `Sensor.id`)
- `temperature_c` (Float, measured temperature in Celsius)
- `maturity_c_hour` (Float, Nurse-Saul cumulative maturity index)
- `simulated_hours` (Float, curing duration elapsed)
- `sensor_status` (Boolean, operational state)
- `data_mode` (String, `"dummy"` or `"real"`)
- `recorded_at` (DateTime, original ThingsBoard timestamp)
- `received_at` (DateTime, backend arrival timestamp)

#### 3. `Alert`
- `id` (Integer, Primary Key)
- `sensor_id` (Integer, Foreign Key -> `Sensor.id`)
- `alert_type` (String, e.g. "DISCONNECT", "TEMP_LIMIT")
- `message` (String, descriptive details)
- `severity` (String, `"low"`, `"medium"`, `"high"`)
- `is_resolved` (Boolean, default False)
- `created_at` (DateTime, event trigger timestamp)

#### 4. `MixProfile`
- `id` (Integer, Primary Key)
- `mix_name` (String, e.g. "C30/37 Rapid Hardening")
- `datum_temperature` (Float, baseline datum, default `-10.0`)
- `target_maturity` (Float, required °C·h before stripping forms)
- `created_at` (DateTime, profile creation date)

---

## 6. REST API Endpoints Specification

### Ingestion (Internal / Webhook)
- `POST /api/v1/telemetry`: Ingests JSON forwarded from ThingsBoard.
- `GET /api/v1/telemetry/health`: Health status check for webhook pipelines.

### Dashboard & Analytics (Frontend Consumption)
- `GET /api/v1/dashboard/summary`: Summary metrics (active sensors, critical alerts, latest status).
- `GET /api/v1/dashboard/latest`: Current state and latest telemetry across sensors.
- `GET /api/v1/dashboard/history`: Time-series concrete temperature and maturity curves filtered by `sensor_id` and date range.

### Sensors & Readings Management
- `GET /api/v1/sensors`: Retrieve registered sensors.
- `POST /api/v1/sensors`: Register a new sensor/device.
- `GET /api/v1/readings`: Paginated log filtered by `sensor_id`, `data_mode`, and timestamps.
- `GET /api/v1/readings/export`: Download data in CSV format.

### Alerts
- `GET /api/v1/alerts`: Query unresolved alerts.
- `PATCH /api/v1/alerts/{id}`: Acknowledge or resolve an active alert.

---

## 7. Phased Implementation Roadmap

1. **Phase 1: Backend Foundation**
   - Initialize repository with `uv`.
   - Setup SQLite engine, SQLAlchemy models, and Pydantic schemas.
   - Verify interactive API docs at `/docs` (Swagger UI).
2. **Phase 2: Ingestion & Cloud Forwarding**
   - Implement `POST /api/v1/telemetry`.
   - Configure ThingsBoard Rule Engine REST API Call Node.
   - Establish public HTTPS tunnel to local backend; verify telemetry persistence.
3. **Phase 3: Dashboard APIs & Business Logic**
   - Implement history, latest status, and summary endpoints.
   - Add alert trigger services for hardware disconnect (`DEVICE_DISCONNECTED_C`).
4. **Phase 4: Frontend Dashboard Integration**
   - Connect web UI via REST requests.
   - Plot live temperature and Nurse-Saul maturity curves.
5. **Phase 5: Hardware Calibration & Production**
   - Toggle firmware to `#define USE_DUMMY_DATA false` and `#define DEMO_MODE false`.
   - Calibrate maturity index curves against cylinder compressive break tests.
