"""Application configuration using pydantic-settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    # Application
    app_name: str = "crypto-morning-brief"
    app_version: str = "0.1.0"
    debug: bool = False
    log_level: str = "INFO"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # API Keys (optional)
    coin_api_key: str | None = None
    binance_api_key: str | None = None

    # Provider selection
    provider: str = "mock"  # Options: "mock", "real"

    # Telegram notification
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None
    send_telegram: bool = False  # Enable/disable Telegram notifications
    telegram_parse_mode: str = "HTML"  # HTML or MarkdownV2
    telegram_wrap_pre: bool = False  # Wrap markdown in <pre> tags

    # Currency settings
    usd_to_krw: float = 1300.0  # USD to KRW exchange rate (default approximate)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
