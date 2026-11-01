"""Application configuration loaded from environment variables via Pydantic Settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ───────────────────────────────────────────────────────────
    APP_NAME: str = "Concrete Maturity API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # ── Database ──────────────────────────────────────────────────────────────
    DATABASE_URL: str = "sqlite+aiosqlite:///./concrete_maturity.db"

    # ── Security ──────────────────────────────────────────────────────────────
    WEBHOOK_API_KEY: str = "change-me-super-secret-key"

    # ── ThingsBoard ───────────────────────────────────────────────────────────
    THINGSBOARD_HOST: str = "mqtt.thingsboard.cloud"
    THINGSBOARD_PORT: int = 1883

    # ThingsBoard REST API credentials
    TB_URL: str = "https://thingsboard.cloud"
    TB_USERNAME: str = ""
    TB_PASSWORD: str = ""
    TB_DEVICE_ID: str = ""

    @property
    def is_tb_configured(self) -> bool:
        """Returns True if all required ThingsBoard REST credentials are set."""
        return bool(
            self.TB_URL.strip()
            and self.TB_USERNAME.strip()
            and self.TB_PASSWORD.strip()
            and self.TB_DEVICE_ID.strip()
        )

    # ── Maturity Defaults ─────────────────────────────────────────────────────
    DEFAULT_DATUM_TEMPERATURE: float = -10.0
    DEFAULT_TARGET_MATURITY: float = 500.0

    # ── CORS ──────────────────────────────────────────────────────────────────
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
