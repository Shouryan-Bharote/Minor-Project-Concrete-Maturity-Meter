"""Datetime utility helpers."""

from datetime import UTC, datetime


def utcnow() -> datetime:
    """Return current UTC time as an aware datetime object."""
    return datetime.now(UTC)


def to_utc(dt: datetime) -> datetime:
    """Ensure a datetime is UTC-aware; treat naive datetimes as UTC."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)
