"""Service layer tests."""

from datetime import datetime

import pytest

from app.models.report import CryptoPrice
from app.providers.dummy import DummyCryptoProvider
from app.services.report_service import ReportService


@pytest.mark.asyncio
async def test_report_service_initialization():
    """Test report service initialization."""
    service = ReportService()
    assert service.provider is not None
    assert isinstance(service.provider, DummyCryptoProvider)


@pytest.mark.asyncio
async def test_generate_daily_report():
    """Test daily report generation."""
    service = ReportService()
    report = await service.generate_daily_report()

    assert report.date is not None
    assert isinstance(report.markdown, str)
    assert len(report.markdown) > 0
    assert "Cryptocurrency Morning Brief" in report.markdown
    assert "Market Summary" in report.markdown
    assert "Top Cryptocurrencies" in report.markdown
    assert "metadata" in report.dict()


@pytest.mark.asyncio
async def test_generate_daily_report_with_date():
    """Test daily report generation with specific date."""
    service = ReportService()
    test_date = datetime(2024, 1, 15, 12, 0, 0)
    report = await service.generate_daily_report(date=test_date)

    assert report.date == test_date
    assert "2024-01-15" in report.markdown


@pytest.mark.asyncio
async def test_generate_daily_report_with_markets():
    """Test daily report generation with specific markets."""
    service = ReportService()
    report = await service.generate_daily_report(include_markets=["BTC", "ETH"])

    assert "BTC" in report.markdown or "ETH" in report.markdown


@pytest.mark.asyncio
async def test_dummy_provider():
    """Test dummy provider functionality."""
    provider = DummyCryptoProvider()
    assert provider.is_available()

    prices = await provider.get_prices(["BTC", "ETH"])
    assert len(prices) == 2
    assert all(isinstance(p, CryptoPrice) for p in prices)
    assert all(p.symbol in ["BTC", "ETH"] for p in prices)

    summary = await provider.get_market_summary()
    assert "total_market_cap" in summary
    assert "total_volume_24h" in summary
    assert "average_change_24h" in summary
