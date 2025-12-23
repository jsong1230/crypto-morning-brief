"""Tests for POST /report/daily API endpoint."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_post_daily_report_default():
    """Test POST /api/v1/report/daily with default parameters."""
    response = client.post(
        "/api/v1/report/daily",
        json={},
    )
    assert response.status_code == 200
    data = response.json()

    assert "date" in data
    assert "markdown" in data
    assert "signals" in data
    assert "regime" in data
    assert isinstance(data["signals"], list)
    assert isinstance(data["regime"], dict)
    assert "label" in data["regime"]


def test_post_daily_report_custom():
    """Test POST /api/v1/report/daily with custom parameters."""
    response = client.post(
        "/api/v1/report/daily",
        json={
            "symbols": ["BTC", "ETH"],
            "keywords": ["bitcoin", "ethereum"],
            "tz": "Asia/Seoul",
        },
    )
    assert response.status_code == 200
    data = response.json()

    assert "date" in data
    assert "markdown" in data
    assert "signals" in data
    assert "regime" in data
    assert "BTC" in data["markdown"] or "ETH" in data["markdown"]


def test_post_daily_report_different_timezone():
    """Test POST /api/v1/report/daily with different timezone."""
    response = client.post(
        "/api/v1/report/daily",
        json={
            "symbols": ["BTC"],
            "keywords": ["bitcoin"],
            "tz": "UTC",
        },
    )
    assert response.status_code == 200
    data = response.json()

    assert "date" in data
    assert "markdown" in data


def test_post_daily_report_invalid_timezone():
    """Test POST /api/v1/report/daily with invalid timezone (should fallback)."""
    response = client.post(
        "/api/v1/report/daily",
        json={
            "symbols": ["BTC"],
            "keywords": ["bitcoin"],
            "tz": "Invalid/Timezone",
        },
    )
    # Should still work but use fallback timezone
    assert response.status_code == 200
    data = response.json()

    assert "date" in data
    assert "markdown" in data


def test_post_daily_report_empty_symbols():
    """Test POST /api/v1/report/daily with empty symbols list."""
    response = client.post(
        "/api/v1/report/daily",
        json={
            "symbols": [],
            "keywords": ["bitcoin"],
        },
    )
    # Should handle gracefully
    assert response.status_code in [200, 400, 502]


def test_post_daily_report_response_structure():
    """Test that response has correct structure."""
    response = client.post(
        "/api/v1/report/daily",
        json={
            "symbols": ["BTC", "ETH"],
            "keywords": ["bitcoin", "ethereum"],
        },
    )
    assert response.status_code == 200
    data = response.json()

    # Check required fields
    required_fields = ["date", "markdown", "signals", "regime"]
    for field in required_fields:
        assert field in data, f"Response should have {field} field"

    # Check signals structure
    if data["signals"]:
        signal = data["signals"][0]
        signal_fields = ["id", "level", "title", "reason", "metric", "threshold", "value"]
        for field in signal_fields:
            assert field in signal, f"Signal should have {field} field"

    # Check regime structure
    assert "label" in data["regime"]
    assert data["regime"]["label"] in ["risk_on", "neutral", "risk_off"]
    assert "rationale" in data["regime"]



