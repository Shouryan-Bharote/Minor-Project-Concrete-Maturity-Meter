# Phase 1: Backend Foundation

## Objectives
- Initialize Python environment with `uv`.
- Build declarative SQLAlchemy models (`Sensor`, `SensorReading`, `Alert`, `MixProfile`).
- Set up Pydantic validation schemas.
- Implement API skeleton: `/telemetry`, `/sensors`, `/dashboard`, `/readings`, `/alerts`.
- Verify database migrations/creation and interactive Swagger docs at `/docs`.

## Acceptance Criteria
- [x] Application launches cleanly via Uvicorn without import errors.
- [x] Database file is created on first startup with all 4 tables.
- [x] Tests pass for health probe, telemetry ingestion, and dashboard routes.
