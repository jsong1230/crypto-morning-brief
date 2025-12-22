"""Report models."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class CryptoPrice(BaseModel):
    """Cryptocurrency price data."""

    symbol: str
    price: float
    change_24h: float = Field(description="24h price change percentage")
    volume_24h: float = Field(description="24h trading volume")
    market_cap: float | None = None


class DailyReportRequest(BaseModel):
    """Request model for daily report generation (legacy)."""

    date: datetime | None = Field(default=None, description="Report date (defaults to today)")
    include_markets: list[str] | None = Field(
        default=None, description="Specific markets to include (defaults to all)"
    )


class DailyReportRequestV2(BaseModel):
    """Request model for daily report generation (v2)."""

    symbols: list[str] = Field(
        default=["BTC", "ETH"],
        description="List of cryptocurrency symbols to include",
    )
    keywords: list[str] = Field(
        default=["bitcoin", "ethereum"],
        description="List of keywords for news search",
    )
    tz: str = Field(
        default="Asia/Seoul",
        description="Timezone for date formatting (e.g., 'Asia/Seoul', 'UTC')",
    )


class DailyReportResponse(BaseModel):
    """Response model for daily report (legacy)."""

    date: datetime
    markdown: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class DailyReportResponseV2(BaseModel):
    """Response model for daily report (v2)."""

    date: str
    markdown: str
    signals: list[dict[str, Any]] = Field(default_factory=list)
    regime: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    telegram_sent: bool = Field(default=False, description="Whether report was sent to Telegram")
