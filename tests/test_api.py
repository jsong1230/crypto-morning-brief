"""API endpoint tests."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data


def test_daily_report_default():
    """Test daily report generation with default parameters."""
    response = client.post("/api/v1/report/daily", json={})
    assert response.status_code == 200
    data = response.json()
    assert "date" in data
    assert "markdown" in data
    assert "signals" in data
    assert "regime" in data
    assert isinstance(data["markdown"], str)
    assert len(data["markdown"]) > 0


def test_daily_report_with_custom_params():
    """Test daily report generation with custom parameters."""
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


def test_daily_report_with_symbols():
    """Test daily report generation with specific symbols."""
    response = client.post(
        "/api/v1/report/daily",
        json={"symbols": ["BTC", "ETH"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert "markdown" in data
    assert "signals" in data
    assert "regime" in data
    # Check that markdown contains requested symbols
    assert "BTC" in data["markdown"] or "ETH" in data["markdown"]
