# Codebase Guide

## Project Layout

```
concrete-maturity-backend/
├── app/
│   ├── main.py                  # ASGI app initialization & lifespan hooks
│   ├── core/
│   │   ├── config.py            # Pydantic BaseSettings (.env loading)
│   │   └── security.py          # Webhook API key validator (X-API-Key)
│   ├── database/
│   │   ├── base.py              # DeclarativeBase class
│   │   └── connection.py        # aiosqlite engine & AsyncSessionLocal dependency
│   ├── models/                  # SQLAlchemy 2.0 ORM Entities
│   │   ├── sensor.py            # Sensors table definition
│   │   ├── sensor_reading.py    # Time-series telemetry readings
│   │   ├── alert.py             # Threshold breaches & sensor disconnect alerts
│   │   └── mix_profile.py       # Concrete mix recipes & target maturity
│   ├── schemas/                 # Pydantic v2 schemas
│   │   ├── telemetry.py         # ThingsBoard payload schema & webhook response
│   │   ├── sensor.py            # Sensor create/update/out schemas
│   │   ├── reading.py           # Reading out & pagination schemas
│   │   └── alert.py             # Alert out & patch resolution schema
│   ├── services/                # Encapsulated business logic
│   │   ├── telemetry_service.py # Telemetry ingestion & default sensor auto-bootstrap
│   │   ├── maturity_service.py  # Nurse-Saul maturity calculations & progress
│   │   └── alert_service.py     # Thermal thresholding & disconnect checks
│   ├── api/
│   │   └── v1/
│   │       ├── router.py        # Central router combining all endpoint modules
│   │       └── endpoints/
│   │           ├── telemetry.py # Ingestion endpoint (/api/v1/telemetry)
│   │           ├── sensors.py   # CRUD for sensors (/api/v1/sensors)
│   │           ├── dashboard.py # Aggregated metrics, latest readings, history curves
│   │           ├── readings.py  # Filtered readings queries & CSV export
│   │           └── alerts.py    # Alert querying & resolution
│   └── utils/
│       └── datetime.py          # UTC datetime helpers
├── tests/
│   ├── test_telemetry.py        # Telemetry ingestion endpoint tests
│   └── test_dashboard.py        # Dashboard endpoint tests
├── docs/                        # Architecture, roadmap, guides, phase specs
├── .agents/                     # Agent execution rules and workflows
├── .state/                      # Cross-session state and progress tracker
├── pyproject.toml               # uv project definitions & dependency matrix
└── .env.example                 # Environment configuration template
```
