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
async def test_public_provider_derivatives_success(public_provider):
    """Test successful derivatives data fetch from Binance."""
    # Mock Binance API responses
    premium_response = {
        "symbol": "BTCUSDT",
        "markPrice": "45000.00",
        "lastFundingRate": "0.0001",
    }
    
    funding_history = [
        {"fundingRate": "0.0001", "fundTime": 1234567890000},
        {"fundingRate": "0.0002", "fundTime": 1234567890000},
        {"fundingRate": "0.0003", "fundTime": 1234567890000},
    ]
    
    oi_response = {
        "symbol": "BTCUSDT",
        "openInterest": "1000.5",
    }
    
    ratio_response = [
        {
            "symbol": "BTCUSDT",
            "longShortRatio": "1.15",
            "timestamp": 1234567890000,
        }
    ]
    
    liquidation_response = [
        {
            "symbol": "BTCUSDT",
            "side": "SELL",
            "executedQty": "10.0",
            "price": "45000.00",
        },
        {
            "symbol": "BTCUSDT",
            "side": "BUY",
            "executedQty": "5.0",
            "price": "45000.00",
        },
    ]
    
    async def mock_get(url, **kwargs):
        class MockResponse:
            def __init__(self, data):
                self._data = data
            
            def json(self):
                return self._data
            
            def raise_for_status(self):
                pass
        
        if "premiumIndex" in url:
            return MockResponse(premium_response)
        elif "fundingRate" in url:
            return MockResponse(funding_history)
        elif "openInterest" in url:
            return MockResponse(oi_response)
        elif "globalLongShortAccountRatio" in url:
            return MockResponse(ratio_response)
        elif "forceOrders" in url:
            return MockResponse(liquidation_response)
        else:
            return MockResponse({})
    
    with patch("app.providers.public_provider.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = mock_get
        mock_client_class.return_value = mock_client
        
        result = await public_provider.get_derivatives_snapshot(["BTC"])
        
        assert "BTC" in result
        assert "funding_rate" in result["BTC"]
        assert "funding_rate_24h" in result["BTC"]
        assert "open_interest" in result["BTC"]
        assert "open_interest_usd" in result["BTC"]
        assert "long_short_ratio" in result["BTC"]
        assert "long_liquidation_24h" in result["BTC"]
        assert "short_liquidation_24h" in result["BTC"]
        assert result["BTC"]["funding_rate"] == 0.0001
        assert result["BTC"]["long_short_ratio"] == 1.15


@pytest.mark.asyncio
async def test_public_provider_derivatives_fallback(public_provider):
    """Test derivatives fallback to mock when API fails."""
    with patch("app.providers.public_provider.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(side_effect=Exception("API Error"))
        mock_client_class.return_value = mock_client
        
        result = await public_provider.get_derivatives_snapshot(["BTC", "ETH"])
        
        # Should fallback to mock provider
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
