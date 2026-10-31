# ESP32 Concrete Maturity Meter & FastAPI Backend

Real-time concrete curing monitoring using the **Nurse-Saul maturity method** ($M = \sum (T_a - T_0)\Delta t$). Ingests telemetry forwarded from ThingsBoard Cloud IoT and serves analytics dashboards for construction site engineers.

---

## Architecture

```
[DS18B20 Temp Sensor]
        │ 1-Wire (GPIO 27, 4.7kΩ pull-up)
        ▼
[ESP32-S3 Microcontroller] ──(I2C: GPIO 20/21)──► [OLED SSD1306 Display]
        │
        │ Wi-Fi + MQTT (v1/devices/me/telemetry)
        ▼
[ThingsBoard Cloud IoT Platform]
        │
        │ Rule Engine Webhook (POST /api/v1/telemetry)
        ▼
[FastAPI Backend Server] (Python 3.12, Uvicorn, Pydantic)
        │
        │ SQLAlchemy 2.0 Async (SQLite)
        ▼
[Frontend Web Dashboard] (Live Status, Time-Series Charts, Mix Analysis)
```

---

## Quickstart

### 1. Requirements
- Python 3.12+
- [`uv`](https://docs.astral.sh/uv/)

### 2. Install Dependencies
```bash
uv sync
```

### 3. Setup Configuration
```bash
cp .env.example .env
```

### 4. Run Development Server
```bash
uv run uvicorn app.main:app --reload --port 8000
```
- Interactive Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Alternative Redoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### 5. Run Test Suite
```bash
uv run pytest
```

---

## API Summary
| Route | Method | Description |
|---|---|---|
| `/api/v1/telemetry` | `POST` | Ingest ThingsBoard webhook telemetry (requires `X-API-Key`) |
| `/api/v1/telemetry/health` | `GET` | Webhook pipeline health check |
| `/api/v1/sensors` | `GET`, `POST` | Sensor inventory CRUD |
| `/api/v1/dashboard/summary` | `GET` | Aggregated counts of sensors, readings, alerts |
| `/api/v1/dashboard/latest` | `GET` | Current telemetry and maturity % per sensor |
| `/api/v1/dashboard/history` | `GET` | Time-series data points for charts |
| `/api/v1/readings` | `GET` | Paginated readings log |
| `/api/v1/readings/export` | `GET` | Download readings as CSV |
| `/api/v1/alerts` | `GET`, `PATCH` | Unresolved alerts & resolution |

---

## Documentation
- [Architecture](docs/ARCHITECTURE.md)
- [Codebase Guide](docs/CODEBASE_GUIDE.md)
- [Component Library](docs/COMPONENT_LIBRARY.md)
- [Development Workflow](docs/DEVELOPMENT_WORKFLOW.md)
- [Project Roadmap](docs/ROADMAP.md)
