"""Telemetry service: ingestion, duplicate detection, and persistence."""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sensor import Sensor
from app.models.sensor_reading import SensorReading
from app.schemas.telemetry import TelemetryPayload


class TelemetryService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def ingest(self, payload: TelemetryPayload) -> SensorReading:
        """
        Persist telemetry. Auto-creates sensor row if sensor_id == 1 and no
        sensor exists yet (bootstrap convenience).

        Raises ValueError if sensor_id is not found.
        """
        # Ensure sensor exists
        sensor = await self.db.get(Sensor, payload.sensor_id)
        if sensor is None:
            if payload.sensor_id == 1:
                # Bootstrap: auto-create default sensor for first run
                sensor = Sensor(
                    id=1,
                    device_name="Concrete Sensor 01",
                    device_id=None,
                    location="Default",
                    is_active=True,
                )
                self.db.add(sensor)
                await self.db.flush()
            else:
                raise ValueError(f"Sensor with id={payload.sensor_id} not found.")

        if payload.recorded_at:
            recorded_at = payload.recorded_at
        elif payload.ts is not None:
            ts_sec = payload.ts / 1000.0 if payload.ts > 1e11 else float(payload.ts)
            recorded_at = datetime.fromtimestamp(ts_sec, tz=UTC)
        else:
            recorded_at = datetime.now(UTC)

        reading = SensorReading(
            sensor_id=payload.sensor_id,
            temperature_c=payload.temperature_c,
            maturity_c_hour=payload.maturity_c_hour,
            simulated_hours=payload.simulated_hours,
            sensor_status=payload.sensor_status,
            data_mode=payload.data_mode,
            recorded_at=recorded_at,
            received_at=datetime.now(UTC),
        )
        self.db.add(reading)
        await self.db.flush()
        await self.db.refresh(reading)
        return reading

    async def get_latest_reading(self, sensor_id: int) -> SensorReading | None:
        """Return the most recent reading for a given sensor."""
        result = await self.db.execute(
            select(SensorReading)
            .where(SensorReading.sensor_id == sensor_id)
            .order_by(SensorReading.received_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
