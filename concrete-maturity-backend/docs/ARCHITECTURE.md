# Architecture Overview

## 1. System Topology
The Concrete Maturity Meter is structured around a 5-tier architecture:

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
        │ Forwarding: POST https://<host>/api/v1/telemetry
        ▼
[FastAPI Backend Server] (Python 3.12, Uvicorn, Pydantic)
        │
        │ SQLAlchemy 2.0 Async ORM (aiosqlite)
        ▼
[SQLite Database] (sensors, sensor_readings, alerts, mix_profiles)
        │
        │ REST API (JSON)
        ▼
[Frontend Web Dashboard] (Live Status, Time-Series Charts, Mix Analysis)
```

## 2. Layer Separation & Boundaries
The backend enforces strict unidirectional dependency flow:
- **Presentation (`app/api/`)**: HTTP endpoints, input parsing, error translation. Depends only on `schemas`, `services`, and `core`.
- **Application Services (`app/services/`)**: Business logic (Nurse-Saul calculations, anomaly detection, ingestion rules). Depends on `models`, `schemas`, and `database`.
- **Domain & Persistence (`app/models/`, `app/database/`)**: Declarative ORM entities, database session lifecycle. No dependency on controllers/API.
- **Cross-cutting (`app/core/`, `app/utils/`)**: Configuration settings, security headers, UTC datetime helpers.
