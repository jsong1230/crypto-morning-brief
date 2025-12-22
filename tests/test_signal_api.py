"""Tests for signal analysis API endpoint."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_signal_analyze_endpoint():
    """Test GET /api/v1/signals/analyze endpoint."""
    response = client.get("/api/v1/signals/analyze?symbols=BTC,ETH")
    assert response.status_code == 200
    data = response.json()

    assert "signals" in data
    assert "regime" in data
    assert "symbols" in data
    assert "timestamp" in data
    assert "signals_count" in data

    assert isinstance(data["signals"], list)
    assert isinstance(data["regime"], dict)
    assert "label" in data["regime"]
    assert "rationale" in data["regime"]
    assert data["regime"]["label"] in ["risk_on", "neutral", "risk_off"]


def test_signal_analyze_endpoint_single_symbol():
    """Test signal analyze endpoint with single symbol."""
    response = client.get("/api/v1/signals/analyze?symbols=BTC")
    assert response.status_code == 200
    data = response.json()

    assert "BTC" in data["symbols"]
    assert len(data["symbols"]) == 1


def test_signal_analyze_endpoint_default():
    """Test signal analyze endpoint with default parameters."""
    response = client.get("/api/v1/signals/analyze")
    assert response.status_code == 200
    data = response.json()

    assert "signals" in data
    assert "regime" in data
