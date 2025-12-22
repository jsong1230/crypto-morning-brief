"""Mock market data provider for development and testing."""

import random
from datetime import datetime, timedelta
from typing import Any

from app.providers.base import MarketProvider


class MockMarketProvider(MarketProvider):
    """Mock provider that returns sample market data for BTC and ETH."""

    # Base prices for spot market
    BASE_PRICES = {
        "BTC": 45000.0,
        "ETH": 2500.0,
    }

    # Base market caps
    BASE_MARKET_CAPS = {
        "BTC": 900_000_000_000,
        "ETH": 300_000_000_000,
    }

    def __init__(self):
        """Initialize mock provider."""
        self._spot_cache: dict[str, dict[str, Any]] = {}
        self._derivatives_cache: dict[str, dict[str, Any]] = {}

    async def get_spot_snapshot(self, symbols: list[str]) -> dict[str, Any]:
        """
        Generate mock spot market snapshot data.

        Args:
            symbols: List of cryptocurrency symbols.

        Returns:
            Dictionary with spot market data for each symbol.
        """
        result: dict[str, Any] = {}

        for symbol in symbols:
            symbol_upper = symbol.upper()
            if symbol_upper not in self.BASE_PRICES:
                continue

            # Use cached data if available and recent, otherwise generate new
            if symbol_upper in self._spot_cache:
                cached = self._spot_cache[symbol_upper]
                # Return cached if less than 1 minute old
                cache_time = cached.get("_timestamp")
                if cache_time and (datetime.utcnow() - cache_time).total_seconds() < 60:  # noqa: DTZ003
                    result[symbol_upper] = {
                        k: v for k, v in cached.items() if not k.startswith("_")
                    }
                    continue

            base_price = self.BASE_PRICES[symbol_upper]
            base_market_cap = self.BASE_MARKET_CAPS.get(symbol_upper, base_price * 20_000_000)

            # Generate random variation (-3% to +3%)
            variation = random.uniform(-0.03, 0.03)
            current_price = base_price * (1 + variation)

            # Generate 24h change (-8% to +8%)
            change_24h = random.uniform(-8.0, 8.0)

            # Generate volume (proportional to price and market cap)
            volume_multiplier = random.uniform(0.02, 0.05)
            volume_24h = base_market_cap * volume_multiplier

            # Update market cap based on price change
            market_cap = base_market_cap * (1 + change_24h / 100)

            spot_data = {
                "price": round(current_price, 2),
                "change_24h": round(change_24h, 2),
                "volume_24h": round(volume_24h, 2),
                "market_cap": round(market_cap, 2),
                "high_24h": round(current_price * random.uniform(1.0, 1.05), 2),
                "low_24h": round(current_price * random.uniform(0.95, 1.0), 2),
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Cache with timestamp
            spot_data["_timestamp"] = datetime.utcnow()
            self._spot_cache[symbol_upper] = spot_data

            result[symbol_upper] = {k: v for k, v in spot_data.items() if not k.startswith("_")}

        return result

    async def get_derivatives_snapshot(self, symbols: list[str]) -> dict[str, Any]:
        """
        Generate mock derivatives market snapshot data.

        Args:
            symbols: List of cryptocurrency symbols.

        Returns:
            Dictionary with derivatives market data for each symbol.
        """
        result: dict[str, Any] = {}

        for symbol in symbols:
            symbol_upper = symbol.upper()
            if symbol_upper not in self.BASE_PRICES:
                continue

            # Use cached data if available and recent
            if symbol_upper in self._derivatives_cache:
                cached = self._derivatives_cache[symbol_upper]
                cache_time = cached.get("_timestamp")
                if cache_time and (datetime.utcnow() - cache_time).total_seconds() < 60:  # noqa: DTZ003
                    result[symbol_upper] = {
                        k: v for k, v in cached.items() if not k.startswith("_")
                    }
                    continue

            # Generate funding rate (-0.1% to 0.1% per 8 hours)
            funding_rate = random.uniform(-0.001, 0.001)
            funding_rate_24h = funding_rate * 3  # 3 periods per day

            # Generate open interest (proportional to market cap)
            base_market_cap = self.BASE_MARKET_CAPS.get(symbol_upper, 100_000_000_000)
            open_interest = base_market_cap * random.uniform(0.1, 0.3)

            # Generate long/short ratio (0.8 to 1.2)
            long_short_ratio = random.uniform(0.8, 1.2)

            # Generate liquidation data
            long_liquidation_24h = random.uniform(10_000_000, 100_000_000)
            short_liquidation_24h = random.uniform(10_000_000, 100_000_000)

            derivatives_data = {
                "funding_rate": round(funding_rate, 6),
                "funding_rate_24h": round(funding_rate_24h, 6),
                "open_interest": round(open_interest, 2),
                "open_interest_usd": round(open_interest, 2),
                "long_short_ratio": round(long_short_ratio, 3),
                "long_liquidation_24h": round(long_liquidation_24h, 2),
                "short_liquidation_24h": round(short_liquidation_24h, 2),
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Cache with timestamp
            derivatives_data["_timestamp"] = datetime.utcnow()
            self._derivatives_cache[symbol_upper] = derivatives_data

            result[symbol_upper] = {
                k: v for k, v in derivatives_data.items() if not k.startswith("_")
            }

        return result

    async def get_news_snapshot(self, keywords: list[str]) -> list[dict[str, Any]]:
        """
        Generate mock news snapshot data.

        Args:
            keywords: List of keywords to search for.

        Returns:
            List of dictionaries with news data.
        """
        news_templates = [
            {
                "title": "{keyword} Price Surges Amid Institutional Adoption",
                "source": "CryptoNews",
                "sentiment": "positive",
            },
            {
                "title": "Market Analysis: {keyword} Shows Strong Technical Indicators",
                "source": "BlockchainDaily",
                "sentiment": "neutral",
            },
            {
                "title": "{keyword} Faces Regulatory Scrutiny in Key Markets",
                "source": "CryptoWatch",
                "sentiment": "negative",
            },
            {
                "title": "Experts Predict {keyword} Will Reach New Highs",
                "source": "DigitalAssets",
                "sentiment": "positive",
            },
            {
                "title": "{keyword} Network Upgrade Scheduled for Next Month",
                "source": "TechCrypto",
                "sentiment": "neutral",
            },
        ]

        result: list[dict[str, Any]] = []
        used_titles = set()

        for keyword in keywords:
            # Generate 2-4 news items per keyword
            num_news = random.randint(2, 4)

            for _ in range(num_news):
                template = random.choice(news_templates)
                title = template["title"].format(keyword=keyword)

                # Avoid duplicate titles
                if title in used_titles:
                    continue
                used_titles.add(title)

                # Generate random publish time (within last 24 hours)
                hours_ago = random.uniform(0, 24)
                published_at = datetime.utcnow() - timedelta(hours=hours_ago)

                news_item = {
                    "title": title,
                    "source": template["source"],
                    "published_at": published_at.isoformat(),
                    "url": f"https://example.com/news/{keyword.lower()}-{random.randint(1000, 9999)}",
                    "sentiment": template["sentiment"],
                    "keywords": [keyword],
                    "summary": f"Latest developments regarding {keyword} in the cryptocurrency market.",
                }

                result.append(news_item)

        # Sort by published_at (newest first)
        result.sort(key=lambda x: x["published_at"], reverse=True)

        return result

    def is_available(self) -> bool:
        """
        Mock provider is always available.

        Returns:
            True
        """
        return True
