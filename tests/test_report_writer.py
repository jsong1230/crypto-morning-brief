"""Tests for ReportWriter."""

import pytest

from app.services.report_writer import ReportWriter


@pytest.fixture
def report_writer():
    """Create ReportWriter instance."""
    return ReportWriter()


@pytest.fixture
def sample_spot_snapshot():
    """Sample spot market data."""
    return {
        "BTC": {
            "price": 45000.0,
            "change_24h": 2.5,
            "volume_24h": 20000000000.0,
            "market_cap": 900000000000.0,
            "high_24h": 46000.0,
            "low_24h": 44000.0,
        },
        "ETH": {
            "price": 2500.0,
            "change_24h": 1.8,
            "volume_24h": 10000000000.0,
            "market_cap": 300000000000.0,
            "high_24h": 2600.0,
            "low_24h": 2400.0,
        },
    }


@pytest.fixture
def sample_derivatives_snapshot():
    """Sample derivatives market data."""
    return {
        "BTC": {
            "funding_rate": 0.0001,
            "funding_rate_24h": 0.0003,
            "open_interest": 120000000000.0,
            "open_interest_usd": 120000000000.0,
            "long_short_ratio": 1.15,
            "long_liquidation_24h": 50000000.0,
            "short_liquidation_24h": 30000000.0,
        },
        "ETH": {
            "funding_rate": -0.0002,
            "funding_rate_24h": -0.0006,
            "open_interest": 50000000000.0,
            "open_interest_usd": 50000000000.0,
            "long_short_ratio": 0.95,
            "long_liquidation_24h": 20000000.0,
            "short_liquidation_24h": 25000000.0,
        },
    }


@pytest.fixture
def sample_signals():
    """Sample signals."""
    return [
        {
            "id": "BTC_funding_overheated",
            "level": "warn",
            "title": "BTC Funding Rate Overheated",
            "reason": "24h funding rate exceeds threshold",
            "metric": "funding_rate_24h",
            "threshold": 0.01,
            "value": 0.015,
        },
        {
            "id": "BTC_volatility_spike",
            "level": "info",
            "title": "BTC Volatility Spike",
            "reason": "24h price change exceeds threshold",
            "metric": "change_24h_abs",
            "threshold": 10.0,
            "value": 12.5,
        },
    ]


@pytest.fixture
def sample_regime():
    """Sample regime."""
    return {
        "label": "neutral",
        "rationale": [
            "BTC: Funding rate elevated",
            "ETH: Low volatility",
        ],
    }


@pytest.fixture
def sample_news():
    """Sample news."""
    return [
        {
            "title": "Bitcoin Price Surges Amid Institutional Adoption",
            "source": "CryptoNews",
            "published_at": "2024-01-15T10:00:00Z",
            "url": "https://example.com/news/bitcoin-1234",
            "sentiment": "positive",
        },
        {
            "title": "Ethereum Network Upgrade Scheduled",
            "source": "TechCrypto",
            "published_at": "2024-01-15T08:00:00Z",
            "url": "https://example.com/news/eth-5678",
            "sentiment": "neutral",
        },
    ]


def test_report_writer_generate_report(
    report_writer,
    sample_spot_snapshot,
    sample_derivatives_snapshot,
    sample_signals,
    sample_regime,
    sample_news,
):
    """Test report generation."""
    date = "2024-01-15"
    report = report_writer.generate_report(
        date=date,
        spot_snapshot=sample_spot_snapshot,
        derivatives_snapshot=sample_derivatives_snapshot,
        signals=sample_signals,
        regime=sample_regime,
        news_snapshot=sample_news,
    )

    assert isinstance(report, str)
    assert len(report) > 0

    # Check title
    assert f"암호화폐 모닝 브리프 — {date} (KST)" in report

    # Check sections
    assert "## 📊 시장 요약" in report
    assert "## 🎯 시장 국면" in report
    assert "## ⚠️ 주요 시그널" in report
    assert "## 📈 주요 지표" in report
    assert "## 📰 뉴스 & 이벤트" in report
    assert "## 🔮 시장 시나리오" in report
    assert "## ⚠️ 면책 조항" in report

    # Check content
    assert "BTC" in report
    assert "ETH" in report


def test_report_writer_with_empty_data(report_writer):
    """Test report generation with empty data."""
    report = report_writer.generate_report(
        date="2024-01-15",
        spot_snapshot={},
        derivatives_snapshot={},
        signals=[],
        regime={"label": "neutral", "rationale": []},
        news_snapshot=[],
    )

    assert isinstance(report, str)
    assert "암호화폐 모닝 브리프" in report
    assert "면책 조항" in report


def test_report_writer_market_summary(report_writer, sample_spot_snapshot):
    """Test market summary generation."""
    summary = report_writer._generate_market_summary(sample_spot_snapshot)

    assert "BTC" in summary
    assert "ETH" in summary
    assert "₩" in summary or "원" in summary  # KRW price formatting
    assert "%" in summary  # Change formatting
