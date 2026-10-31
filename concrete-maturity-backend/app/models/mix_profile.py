"""ORM model: MixProfile – concrete mix recipe with maturity targets."""

from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class MixProfile(Base):
    __tablename__ = "mix_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    mix_name: Mapped[str] = mapped_column(String(256), nullable=False, comment="e.g. C30/37 Rapid Hardening")
    datum_temperature: Mapped[float] = mapped_column(
        Float, nullable=False, default=-10.0, comment="Nurse-Saul datum temperature (°C)"
    )
    target_maturity: Mapped[float] = mapped_column(
        Float, nullable=False, comment="Required maturity index (°C·h) before stripping formwork"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )

    def __repr__(self) -> str:
        return f"<MixProfile id={self.id} name={self.mix_name!r} target={self.target_maturity}°C·h>"
