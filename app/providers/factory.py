"""Provider factory for dependency injection."""

from app.config import settings
from app.providers.base import MarketProvider
from app.providers.mock_provider import MockMarketProvider
from app.providers.public_provider import PublicProvider
from app.utils.logger import logger


def get_market_provider() -> MarketProvider:
    """
    Factory function to get market provider based on settings.

    Returns:
        MarketProvider instance based on settings.PROVIDER value.
    """
    provider_type = settings.provider.lower()

    if provider_type == "mock":
        logger.info("Using MockMarketProvider")
        return MockMarketProvider()
    elif provider_type == "public":
        logger.info("Using PublicProvider (CoinGecko API)")
        return PublicProvider()
    elif provider_type == "real":
        # TODO: Implement real provider when ready
        logger.warning("Real provider not implemented yet, falling back to mock")
        return MockMarketProvider()
    else:
        logger.warning(f"Unknown provider type '{provider_type}', using mock")
        return MockMarketProvider()
