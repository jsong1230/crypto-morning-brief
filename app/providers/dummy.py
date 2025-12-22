"""Dummy data provider for development and testing."""

import random
from datetime import datetime
from typing import Any

from app.models.report import CryptoPrice
from app.providers.base import CryptoDataProvider


class DummyCryptoProvider(CryptoDataProvider):
    """Dummy provider that returns mock cryptocurrency data."""

    # Popular cryptocurrencies with base prices
    DEFAULT_SYMBOLS = {
        "BTC": 45000.0,
        "ETH": 2500.0,
        "BNB": 300.0,
        "SOL": 100.0,
        "ADA": 0.5,
        "XRP": 0.6,
        "DOGE": 0.08,
        "DOT": 7.0,
        "MATIC": 0.9,
        "AVAX": 35.0,
    }

    def __init__(self):
        """Initialize dummy provider."""
        self._base_prices = self.DEFAULT_SYMBOLS.copy()

    async def get_prices(self, symbols: list[str] | None = None) -> list[CryptoPrice]:
        """
        Generate dummy price data.

        Args:
            symbols: List of symbols to fetch. If None, returns all default symbols.

        Returns:
            List of CryptoPrice objects with randomized data.
        """
        if symbols is None:
            symbols = list(self.DEFAULT_SYMBOLS.keys())

        prices = []
        for symbol in symbols:
            if symbol.upper() not in self.DEFAULT_SYMBOLS:
                continue

            base_price = self._base_prices[symbol.upper()]
            # Generate random variation (-5% to +5%)
            variation = random.uniform(-0.05, 0.05)
            current_price = base_price * (1 + variation)

            # Update base price for next call (simulate price movement)
            self._base_prices[symbol.upper()] = current_price

            # Generate 24h change (-10% to +10%)
            change_24h = random.uniform(-10.0, 10.0)

            # Generate volume (proportional to price)
            volume_24h = current_price * random.uniform(1000000, 10000000)

            # Generate market cap (rough estimate)
            market_cap = current_price * random.uniform(10000000, 100000000)

            prices.append(
                CryptoPrice(
                    symbol=symbol.upper(),
                    price=round(current_price, 2),
                    change_24h=round(change_24h, 2),
                    volume_24h=round(volume_24h, 2),
                    market_cap=round(market_cap, 2),
                )
            )

        return prices

    async def get_market_summary(self) -> dict[str, Any]:
        """
        Generate dummy market summary.

        Returns:
            Dictionary with market summary data.
        """
        prices = await self.get_prices()
        total_market_cap = sum(p.market_cap or 0 for p in prices)
        avg_change = sum(p.change_24h for p in prices) / len(prices) if prices else 0

        return {
            "total_market_cap": round(total_market_cap, 2),
            "total_volume_24h": round(sum(p.volume_24h for p in prices), 2),
            "average_change_24h": round(avg_change, 2),
            "total_cryptocurrencies": len(prices),
            "timestamp": datetime.utcnow().isoformat(),
        }

    def is_available(self) -> bool:
        """
        Dummy provider is always available.

        Returns:
            True
        """
        return True
