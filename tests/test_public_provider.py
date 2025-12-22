"""Tests for PublicProvider."""

from unittest.mock import AsyncMock, patch

import pytest

from app.providers.public_provider import PublicProvider


@pytest.fixture
def public_provider():
    """Create PublicProvider instance."""
    return PublicProvider()


@pytest.mark.asyncio
async def test_public_provider_spot_success(public_provider):
    """Test successful spot data fetch from CoinGecko."""
    mock_response_data = {
        "bitcoin": {
            "usd": 45000.0,
            "usd_24h_change": 2.5,
            "usd_24h_vol": 20000000000.0,
            "usd_market_cap": 900000000000.0,
            "usd_24h_high": 46000.0,
            "usd_24h_low": 44000.0,
        },
        "ethereum": {
            "usd": 2500.0,
            "usd_24h_change": 1.8,
            "usd_24h_vol": 10000000000.0,
            "usd_market_cap": 300000000000.0,
            "usd_24h_high": 2600.0,
            "usd_24h_low": 2400.0,
        },
    }

    class MockResponse:
        def json(self):
            return mock_response_data

        def raise_for_status(self):
            pass

    async def mock_get(*args, **kwargs):
        return MockResponse()

    with patch("app.providers.public_provider.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = mock_get
        mock_client_class.return_value = mock_client

        result = await public_provider.get_spot_snapshot(["BTC", "ETH"])

        assert "BTC" in result
        assert "ETH" in result
        assert result["BTC"]["price"] == 45000.0
        assert result["BTC"]["change_24h"] == 2.5
        assert result["ETH"]["price"] == 2500.0


@pytest.mark.asyncio
async def test_public_provider_spot_fallback(public_provider):
    """Test fallback to mock when API fails."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(side_effect=Exception("API Error"))
        mock_client_class.return_value = mock_client

        result = await public_provider.get_spot_snapshot(["BTC", "ETH"])

        # Should fallback to mock provider
        assert "BTC" in result or "ETH" in result


@pytest.mark.asyncio
async def test_public_provider_derivatives_fallback(public_provider):
    """Test derivatives fallback to mock."""
    result = await public_provider.get_derivatives_snapshot(["BTC", "ETH"])

    # Should use mock provider
    assert "BTC" in result or "ETH" in result


@pytest.mark.asyncio
async def test_public_provider_news_fallback(public_provider):
    """Test news fallback to mock."""
    result = await public_provider.get_news_snapshot(["Bitcoin"])

    # Should use mock provider
    assert isinstance(result, list)


def test_public_provider_is_available(public_provider):
    """Test provider availability check."""
    assert public_provider.is_available() is True


@pytest.mark.asyncio
async def test_public_provider_invalid_symbol(public_provider):
    """Test with invalid symbol."""

    class MockResponse:
        def json(self):
            return {}

        def raise_for_status(self):
            pass

    async def mock_get(*args, **kwargs):
        return MockResponse()

    with patch("app.providers.public_provider.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = mock_get
        mock_client_class.return_value = mock_client

        result = await public_provider.get_spot_snapshot(["INVALID"])

        # Should fallback to mock
        assert isinstance(result, dict)
