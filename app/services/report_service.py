"""Report generation service."""

from datetime import datetime
from typing import Any

from app.models.report import CryptoPrice, DailyReportResponse
from app.providers.base import CryptoDataProvider
from app.providers.dummy import DummyCryptoProvider
from app.utils.logger import logger


class ReportService:
    """Service for generating cryptocurrency reports."""

    def __init__(self, provider: CryptoDataProvider | None = None):
        """
        Initialize report service.

        Args:
            provider: CryptoDataProvider instance. If None, uses DummyCryptoProvider.
        """
        self.provider = provider or DummyCryptoProvider()
        logger.info(f"ReportService initialized with provider: {type(self.provider).__name__}")

    async def generate_daily_report(
        self, date: datetime | None = None, include_markets: list[str] | None = None
    ) -> DailyReportResponse:
        """
        Generate a daily cryptocurrency report in Markdown format.

        Args:
            date: Report date. If None, uses current date.
            include_markets: List of specific markets to include. If None, includes all.

        Returns:
            DailyReportResponse with Markdown content.
        """
        if date is None:
            date = datetime.utcnow()

        logger.info(f"Generating daily report for {date.date()}")

        # Fetch data from provider
        prices = await self.provider.get_prices(symbols=include_markets)
        market_summary = await self.provider.get_market_summary()

        # Generate Markdown report
        markdown = self._generate_markdown(date, prices, market_summary)

        metadata = {
            "provider": type(self.provider).__name__,
            "symbols_count": len(prices),
            "generated_at": datetime.utcnow().isoformat(),
        }

        return DailyReportResponse(date=date, markdown=markdown, metadata=metadata)

    def _generate_markdown(
        self, date: datetime, prices: list[CryptoPrice], market_summary: dict[str, Any]
    ) -> str:
        """
        Generate Markdown content from data.

        Args:
            date: Report date.
            prices: List of cryptocurrency prices.
            market_summary: Market summary data.

        Returns:
            Markdown formatted string.
        """
        lines = [
            "# Cryptocurrency Morning Brief",
            f"**Date:** {date.strftime('%Y-%m-%d')}",
            "",
            "---",
            "",
            "## Market Summary",
            "",
            f"- **Total Market Cap:** ${market_summary['total_market_cap']:,.2f}",
            f"- **Total 24h Volume:** ${market_summary['total_volume_24h']:,.2f}",
            f"- **Average 24h Change:** {market_summary['average_change_24h']:.2f}%",
            f"- **Total Cryptocurrencies:** {market_summary['total_cryptocurrencies']}",
            "",
            "---",
            "",
            "## Top Cryptocurrencies",
            "",
            "| Symbol | Price (USD) | 24h Change | 24h Volume | Market Cap |",
            "|--------|-------------|------------|------------|------------|",
        ]

        # Sort by market cap (descending)
        sorted_prices = sorted(prices, key=lambda p: p.market_cap or 0, reverse=True)

        for price in sorted_prices:
            change_emoji = "📈" if price.change_24h >= 0 else "📉"
            change_str = f"{change_emoji} {price.change_24h:+.2f}%"
            volume_str = f"${price.volume_24h:,.2f}"
            market_cap_str = f"${price.market_cap:,.2f}" if price.market_cap else "N/A"

            lines.append(
                f"| {price.symbol} | ${price.price:,.2f} | {change_str} | {volume_str} | {market_cap_str} |"
            )

        lines.extend(
            [
                "",
                "---",
                "",
                f"*Report generated at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}*",
            ]
        )

        return "\n".join(lines)
