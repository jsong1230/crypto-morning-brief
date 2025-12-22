"""Base provider interface."""

from abc import ABC, abstractmethod
from typing import Any

from app.models.report import CryptoPrice


class CryptoDataProvider(ABC):
    """Abstract base class for cryptocurrency data providers."""

    @abstractmethod
    async def get_prices(self, symbols: list[str] | None = None) -> list[CryptoPrice]:
        """
        Fetch cryptocurrency prices.

        Args:
            symbols: List of cryptocurrency symbols (e.g., ['BTC', 'ETH']).
                    If None, returns all available symbols.

        Returns:
            List of CryptoPrice objects.
        """
        pass

    @abstractmethod
    async def get_market_summary(self) -> dict[str, Any]:
        """
        Get overall market summary.

        Returns:
            Dictionary containing market summary data.
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the provider is available and configured.

        Returns:
            True if provider is available, False otherwise.
        """
        pass


class MarketProvider(ABC):
    """Abstract base class for market data providers."""

    @abstractmethod
    async def get_spot_snapshot(self, symbols: list[str]) -> dict[str, Any]:
        """
        Get spot market snapshot data.

        Args:
            symbols: List of cryptocurrency symbols (e.g., ['BTC', 'ETH']).

        Returns:
            Dictionary with standardized spot market data.
            Format: {
                'symbol': {
                    'price': float,
                    'change_24h': float,
                    'volume_24h': float,
                    'market_cap': float,
                    ...
                },
                ...
            }
        """
        pass

    @abstractmethod
    async def get_derivatives_snapshot(self, symbols: list[str]) -> dict[str, Any]:
        """
        Get derivatives market snapshot data.

        Args:
            symbols: List of cryptocurrency symbols (e.g., ['BTC', 'ETH']).

        Returns:
            Dictionary with standardized derivatives market data.
            Format: {
                'symbol': {
                    'funding_rate': float,
                    'open_interest': float,
                    'long_short_ratio': float,
                    'funding_rate_24h': float,
                    ...
                },
                ...
            }
        """
        pass

    @abstractmethod
    async def get_news_snapshot(self, keywords: list[str]) -> list[dict[str, Any]]:
        """
        Get news snapshot data.

        Args:
            keywords: List of keywords to search for (e.g., ['Bitcoin', 'Ethereum']).

        Returns:
            List of dictionaries with standardized news data.
            Format: [
                {
                    'title': str,
                    'source': str,
                    'published_at': str,
                    'url': str,
                    'sentiment': str,
                    ...
                },
                ...
            ]
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the provider is available and configured.

        Returns:
            True if provider is available, False otherwise.
        """
        pass
