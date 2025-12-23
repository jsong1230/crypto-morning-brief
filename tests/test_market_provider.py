"""Tests for MarketProvider and related endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.providers.mock_provider import MockMarketProvider

client = TestClient(app)


@pytest.mark.asyncio
async def test_mock_market_provider_spot():
    """Test MockMarketProvider get_spot_snapshot."""
    provider = MockMarketProvider()
    result = await provider.get_spot_snapshot(["BTC", "ETH"])

    assert "BTC" in result
    assert "ETH" in result
    assert "price" in result["BTC"]
    assert "change_24h" in result["BTC"]
    assert "volume_24h" in result["BTC"]
    assert "market_cap" in result["BTC"]


@pytest.mark.asyncio
async def test_mock_market_provider_derivatives():
    """Test MockMarketProvider get_derivatives_snapshot."""
    provider = MockMarketProvider()
    result = await provider.get_derivatives_snapshot(["BTC", "ETH"])

    assert "BTC" in result
    assert "ETH" in result
    assert "funding_rate" in result["BTC"]
    assert "open_interest" in result["BTC"]
    assert "long_short_ratio" in result["BTC"]


@pytest.mark.asyncio
async def test_mock_market_provider_news():
    """Test MockMarketProvider get_news_snapshot."""
    provider = MockMarketProvider()
    result = await provider.get_news_snapshot(["Bitcoin", "Ethereum"])

    assert isinstance(result, list)
    assert len(result) > 0
    assert "title" in result[0]
    assert "source" in result[0]
    assert "published_at" in result[0]


def test_api_spot_snapshot():
    """Test GET /api/v1/market/spot endpoint."""
    response = client.get("/api/v1/market/spot?symbols=BTC,ETH")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "symbols" in data
    assert "BTC" in data["data"]
    assert "ETH" in data["data"]


def test_api_derivatives_snapshot():
    """Test GET /api/v1/market/derivatives endpoint."""
    response = client.get("/api/v1/market/derivatives?symbols=BTC")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "symbols" in data
    assert "BTC" in data["data"]


def test_api_news_snapshot():
    """Test GET /api/v1/market/news endpoint."""
    response = client.get("/api/v1/market/news?keywords=Bitcoin")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "keywords" in data
    assert "count" in data
    assert isinstance(data["data"], list)



