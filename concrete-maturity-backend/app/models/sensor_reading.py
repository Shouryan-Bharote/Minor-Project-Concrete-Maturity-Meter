"""ORM model: SensorReading – one telemetry data point from a sensor."""

from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sensor_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sensors.id", ondelete="CASCADE"), nullable=False, index=True
    )
    temperature_c: Mapped[float] = mapped_column(Float, nullable=False, comment="Measured temperature in Celsius")
    maturity_c_hour: Mapped[float] = mapped_column(Float, nullable=False, comment="Nurse-Saul cumulative maturity index (°C·h)")
    simulated_hours: Mapped[float] = mapped_column(Float, nullable=False, comment="Curing duration elapsed in hours")
    sensor_status: Mapped[bool] = mapped_column(Boolean, nullable=False, comment="True if sensor is operational")
    data_mode: Mapped[str] = mapped_column(String(16), nullable=False, default="real", comment="'dummy' or 'real'")
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, comment="Original ThingsBoard timestamp"
    )
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        comment="Backend arrival timestamp",
    )

    # Relationships
    sensor: Mapped["Sensor"] = relationship("Sensor", back_populates="readings")  # noqa: F821

    def __repr__(self) -> str:
        return (
            f"<SensorReading id={self.id} sensor_id={self.sensor_id} "
            f"temp={self.temperature_c}°C maturity={self.maturity_c_hour}°C·h>"
        )
