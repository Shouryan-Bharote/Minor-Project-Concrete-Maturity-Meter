"""Maturity service: target progress calculation using Nurse-Saul method."""

from app.core.config import settings


class MaturityService:
    """Stateless helper for maturity index calculations."""

    @staticmethod
    def progress_percent(
        current_maturity: float,
        target_maturity: float | None = None,
    ) -> float:
        """
        Return progress toward target maturity as a percentage (0–100).

        Args:
            current_maturity: Current cumulative maturity index (°C·h).
            target_maturity: Required maturity before stripping formwork (°C·h).
                             Defaults to DEFAULT_TARGET_MATURITY from settings.

        Returns:
            Progress percentage clamped to [0.0, 100.0].
        """
        target = target_maturity or settings.DEFAULT_TARGET_MATURITY
        if target <= 0:
            return 100.0
        return min(100.0, (current_maturity / target) * 100.0)

    @staticmethod
    def nurse_saul_increment(temperature_c: float, delta_t_hours: float, datum: float = -10.0) -> float:
        """
        Compute a single Nurse-Saul maturity increment.

        M_increment = (T_a - T_0) * Δt

        Args:
            temperature_c: Measured concrete temperature (°C).
            delta_t_hours: Time interval (hours).
            datum: Datum temperature T_0 (default -10.0°C).

        Returns:
            Maturity increment in °C·h (clamped to 0 if temperature below datum).
        """
        increment = (temperature_c - datum) * delta_t_hours
        return max(0.0, increment)
