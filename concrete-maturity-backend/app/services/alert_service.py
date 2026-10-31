"""Alert service: threshold checks and sensor disconnect detection."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert
from app.models.sensor_reading import SensorReading

# Thresholds
MAX_TEMP_C = 70.0          # Alert if concrete exceeds 70°C
MIN_TEMP_C = -5.0          # Alert if concrete drops below -5°C
DISCONNECT_THRESHOLD_MIN = 5  # Alert if no reading received in N minutes


class AlertService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def check_temperature(self, reading: SensorReading) -> Alert | None:
        """Create a TEMP_LIMIT alert if temperature is out of range."""
        if reading.temperature_c > MAX_TEMP_C:
            return await self._create_alert(
                sensor_id=reading.sensor_id,
                alert_type="TEMP_LIMIT",
                message=f"Temperature {reading.temperature_c:.1f}°C exceeds maximum {MAX_TEMP_C}°C.",
                severity="high",
            )
        if reading.temperature_c < MIN_TEMP_C:
            return await self._create_alert(
                sensor_id=reading.sensor_id,
                alert_type="TEMP_LIMIT",
                message=f"Temperature {reading.temperature_c:.1f}°C is below minimum {MIN_TEMP_C}°C.",
                severity="medium",
            )
        return None

    async def check_disconnect(self, sensor_id: int) -> Alert | None:
        """
        Raise a DISCONNECT alert if the sensor hasn't sent data recently.
        Called periodically (e.g., via a scheduled job or on dashboard load).
        """
        threshold_time = datetime.now(UTC) - timedelta(minutes=DISCONNECT_THRESHOLD_MIN)
        result = await self.db.execute(
            select(SensorReading)
            .where(SensorReading.sensor_id == sensor_id)
            .where(SensorReading.received_at >= threshold_time)
            .limit(1)
        )
        if result.scalar_one_or_none() is None:
            return await self._create_alert(
                sensor_id=sensor_id,
                alert_type="DISCONNECT",
                message=f"No data received from sensor {sensor_id} in the last {DISCONNECT_THRESHOLD_MIN} minutes.",
                severity="high",
            )
        return None

    async def _create_alert(
        self,
        sensor_id: int,
        alert_type: str,
        message: str,
        severity: str,
    ) -> Alert:
        alert = Alert(
            sensor_id=sensor_id,
            alert_type=alert_type,
            message=message,
            severity=severity,
            is_resolved=False,
        )
        self.db.add(alert)
        await self.db.flush()
        await self.db.refresh(alert)
        return alert
