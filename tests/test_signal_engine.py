"""Tests for SignalEngine."""

import pytest

from app.services.signal_engine import SignalEngine


@pytest.fixture
def signal_engine():
    """Create SignalEngine instance for testing."""
    return SignalEngine()


@pytest.fixture
def sample_spot_snapshot():
    """Sample spot market data."""
    return {
        "BTC": {
            "price": 45000.0,
            "change_24h": 12.0,  # High volatility
            "volume_24h": 20000000000.0,
            "market_cap": 900000000000.0,
            "high_24h": 46000.0,
            "low_24h": 44000.0,
        },
        "ETH": {
            "price": 2500.0,
            "change_24h": -6.0,
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
            "funding_rate": 0.012,  # Overheated
            "funding_rate_24h": 0.015,  # Overheated
            "open_interest": 120000000000.0,
            "open_interest_usd": 120000000000.0,
            "long_short_ratio": 1.6,  # Extreme
            "long_liquidation_24h": 50000000.0,
            "short_liquidation_24h": 30000000.0,
        },
        "ETH": {
            "funding_rate": -0.0005,
            "funding_rate_24h": -0.001,
            "open_interest": 50000000000.0,
            "open_interest_usd": 50000000000.0,
            "long_short_ratio": 0.9,
            "long_liquidation_24h": 20000000.0,
            "short_liquidation_24h": 25000000.0,
        },
    }


def test_signal_engine_analyze_basic(
    signal_engine, sample_spot_snapshot, sample_derivatives_snapshot
):
    """Test basic signal engine analysis."""
    result = signal_engine.analyze(sample_spot_snapshot, sample_derivatives_snapshot)

    assert "signals" in result
    assert "regime" in result
    assert "timestamp" in result
    assert isinstance(result["signals"], list)
    assert isinstance(result["regime"], dict)
    assert "label" in result["regime"]
    assert "rationale" in result["regime"]


def test_signal_engine_detects_funding_overheated(
    signal_engine, sample_spot_snapshot, sample_derivatives_snapshot
):
    """Test that signal engine detects funding rate overheating."""
    # BTC has funding_rate_24h = 0.015 (1.5%), which exceeds threshold
    result = signal_engine.analyze(sample_spot_snapshot, sample_derivatives_snapshot)

    # Find funding-related signals
    funding_signals = [s for s in result["signals"] if "funding" in s["id"].lower()]

    assert len(funding_signals) > 0, "Should detect funding rate signals"
    assert any(s["level"] in ["warn", "critical"] for s in funding_signals), (
        "Should have warn or critical level"
    )


def test_signal_engine_detects_volatility_spike(
    signal_engine, sample_spot_snapshot, sample_derivatives_snapshot
):
    """Test that signal engine detects volatility spikes."""
    # BTC has change_24h = 12%, which exceeds threshold
    result = signal_engine.analyze(sample_spot_snapshot, sample_derivatives_snapshot)

    # Find volatility signals
    volatility_signals = [s for s in result["signals"] if "volatility" in s["id"].lower()]

    assert len(volatility_signals) > 0, "Should detect volatility spike"
    assert any(s["level"] in ["warn", "critical"] for s in volatility_signals), (
        "Should have warn or critical level"
    )


def test_signal_engine_regime_determination(
    signal_engine, sample_spot_snapshot, sample_derivatives_snapshot
):
    """Test that signal engine determines market regime correctly."""
    result = signal_engine.analyze(sample_spot_snapshot, sample_derivatives_snapshot)

    regime = result["regime"]
    assert regime["label"] in ["risk_on", "neutral", "risk_off"]
    assert isinstance(regime["rationale"], list)
    assert len(regime["rationale"]) > 0


def test_signal_engine_signal_format(
    signal_engine, sample_spot_snapshot, sample_derivatives_snapshot
):
    """Test that signals have correct format."""
    result = signal_engine.analyze(sample_spot_snapshot, sample_derivatives_snapshot)

    if result["signals"]:
        signal = result["signals"][0]
        required_fields = ["id", "level", "title", "reason", "metric", "threshold", "value"]
        for field in required_fields:
            assert field in signal, f"Signal should have {field} field"
        assert signal["level"] in ["info", "warn", "critical"]


def test_signal_engine_with_extreme_data():
    """Test signal engine with extreme market conditions."""
    engine = SignalEngine()

    # Extreme conditions
    spot = {
        "BTC": {
            "price": 50000.0,
            "change_24h": 20.0,  # Extreme volatility
            "volume_24h": 50000000000.0,
            "market_cap": 1000000000000.0,
            "high_24h": 52000.0,
            "low_24h": 48000.0,
        },
    }

    deriv = {
        "BTC": {
            "funding_rate": 0.06,  # Extreme funding
            "funding_rate_24h": 0.08,  # Extreme funding
            "open_interest": 150000000000.0,
            "open_interest_usd": 150000000000.0,
            "long_short_ratio": 2.0,  # Extreme
            "long_liquidation_24h": 200000000.0,
            "short_liquidation_24h": 100000000.0,
        },
    }

    result = engine.analyze(spot, deriv)

    # Should detect multiple critical signals
    critical_signals = [s for s in result["signals"] if s["level"] == "critical"]
    assert len(critical_signals) > 0, "Should detect critical signals in extreme conditions"

    # Regime should be risk_off
    assert result["regime"]["label"] == "risk_off", (
        "Extreme conditions should result in risk_off regime"
    )
