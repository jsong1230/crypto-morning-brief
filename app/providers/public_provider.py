"""Public API provider using free endpoints (CoinGecko)."""

from datetime import datetime
from typing import Any

import httpx

from app.providers.base import MarketProvider
from app.providers.mock_provider import MockMarketProvider
from app.utils.logger import logger

# CoinGecko API endpoints (free, no API key required)
COINGECKO_API_BASE = "https://api.coingecko.com/api/v3"
COINGECKO_SIMPLE_PRICE = f"{COINGECKO_API_BASE}/simple/price"
COINGECKO_COINS = f"{COINGECKO_API_BASE}/coins"

# Symbol mapping: our symbols -> CoinGecko IDs
SYMBOL_TO_COINGECKO_ID = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "BNB": "binancecoin",
    "SOL": "solana",
    "ADA": "cardano",
    "XRP": "ripple",
    "DOGE": "dogecoin",
    "DOT": "polkadot",
    "MATIC": "matic-network",
    "AVAX": "avalanche-2",
}


class PublicProvider(MarketProvider):
    """Provider using public APIs (CoinGecko) for real market data."""

    def __init__(self):
        """Initialize public provider with fallback to mock."""
        self._fallback_provider = MockMarketProvider()
        self._http_timeout = 10.0

    async def get_spot_snapshot(self, symbols: list[str]) -> dict[str, Any]:
        """
        Get spot market snapshot from CoinGecko API.

        Args:
            symbols: List of cryptocurrency symbols.

        Returns:
            Dictionary with spot market data, or fallback to mock if API fails.
        """
        try:
            # Map symbols to CoinGecko IDs
            coin_ids = []
            symbol_map = {}  # coin_id -> symbol
            for symbol in symbols:
                symbol_upper = symbol.upper()
                if symbol_upper in SYMBOL_TO_COINGECKO_ID:
                    coin_id = SYMBOL_TO_COINGECKO_ID[symbol_upper]
                    coin_ids.append(coin_id)
                    symbol_map[coin_id] = symbol_upper

            if not coin_ids:
                logger.warning("No valid symbols found, using fallback")
                return await self._fallback_provider.get_spot_snapshot(symbols)

            # Fetch data from CoinGecko
            async with httpx.AsyncClient(timeout=self._http_timeout) as client:
                # Get simple price data
                params = {
                    "ids": ",".join(coin_ids),
                    "vs_currencies": "usd",
                    "include_24hr_change": "true",
                    "include_24hr_vol": "true",
                    "include_market_cap": "true",
                    "include_24hr_high": "true",
                    "include_24hr_low": "true",
                }

                response = await client.get(COINGECKO_SIMPLE_PRICE, params=params)
                response.raise_for_status()
                price_data = response.json()

            # Transform CoinGecko data to our format
            result: dict[str, Any] = {}
            for coin_id, data in price_data.items():
                if coin_id not in symbol_map:
                    continue

                symbol = symbol_map[coin_id]
                result[symbol] = {
                    "price": data.get("usd", 0.0),
                    "change_24h": data.get("usd_24h_change", 0.0) or 0.0,
                    "volume_24h": data.get("usd_24h_vol", 0.0) or 0.0,
                    "market_cap": data.get("usd_market_cap", 0.0) or 0.0,
                    "high_24h": data.get("usd_24h_high", 0.0) or 0.0,
                    "low_24h": data.get("usd_24h_low", 0.0) or 0.0,
                    "timestamp": datetime.utcnow().isoformat(),
                }

            if result:
                logger.info(
                    f"Successfully fetched spot data for {len(result)} symbols from CoinGecko"
                )
                return result
            else:
                logger.warning("No data returned from CoinGecko, using fallback")
                return await self._fallback_provider.get_spot_snapshot(symbols)

        except httpx.HTTPStatusError as e:
            logger.warning(
                f"CoinGecko API returned error: {e.response.status_code}, using fallback"
            )
            return await self._fallback_provider.get_spot_snapshot(symbols)
        except httpx.RequestError as e:
            logger.warning(f"CoinGecko API request failed: {str(e)}, using fallback")
            return await self._fallback_provider.get_spot_snapshot(symbols)
        except Exception as e:
            logger.warning(f"Unexpected error fetching from CoinGecko: {str(e)}, using fallback")
            return await self._fallback_provider.get_spot_snapshot(symbols)

    async def get_derivatives_snapshot(self, symbols: list[str]) -> dict[str, Any]:
        """
        Get derivatives snapshot (fallback to mock).

        Args:
            symbols: List of cryptocurrency symbols.

        Returns:
            Dictionary with derivatives data from mock provider.
        """
        logger.info("Derivatives data not available from public API, using mock fallback")
        return await self._fallback_provider.get_derivatives_snapshot(symbols)

    async def get_news_snapshot(self, keywords: list[str]) -> list[dict[str, Any]]:
        """
        Get news snapshot (fallback to mock).

        Args:
            keywords: List of keywords.

        Returns:
            List of news items from mock provider.
        """
        logger.info("News data not available from public API, using mock fallback")
        return await self._fallback_provider.get_news_snapshot(keywords)

    def is_available(self) -> bool:
        """
        Check if provider is available.

        Returns:
            True (public API is always available, though may fail at runtime).
        """
        return True
