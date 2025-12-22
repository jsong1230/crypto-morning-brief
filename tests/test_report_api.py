"""Tests for morning brief report API endpoint."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_morning_brief_endpoint():
    """Test GET /api/v1/report/morning-brief endpoint."""
    response = client.get("/api/v1/report/morning-brief")
    assert response.status_code == 200
    data = response.json()

    assert "date" in data
    assert "markdown" in data
    assert "metadata" in data
    assert isinstance(data["markdown"], str)
    assert len(data["markdown"]) > 0

    # Check markdown content
    assert "암호화폐 모닝 브리프" in data["markdown"]
    assert "시장 요약" in data["markdown"]
    assert "시장 국면" in data["markdown"]
    assert "주요 시그널" in data["markdown"]
    assert "주요 지표" in data["markdown"]
    assert "뉴스 & 이벤트" in data["markdown"]
    assert "시장 시나리오" in data["markdown"]
    assert "면책 조항" in data["markdown"]


def test_morning_brief_with_date():
    """Test morning brief with specific date."""
    response = client.get("/api/v1/report/morning-brief?date=2024-01-15")
    assert response.status_code == 200
    data = response.json()

    assert data["date"] == "2024-01-15"
    assert "2024-01-15" in data["markdown"]


def test_morning_brief_with_custom_symbols():
    """Test morning brief with custom symbols."""
    response = client.get("/api/v1/report/morning-brief?symbols=BTC")
    assert response.status_code == 200
    data = response.json()

    assert "BTC" in data["markdown"]
    assert "metadata" in data
    assert "BTC" in data["metadata"]["symbols"]


def test_morning_brief_invalid_date():
    """Test morning brief with invalid date format."""
    response = client.get("/api/v1/report/morning-brief?date=invalid-date")
    assert response.status_code == 400
    assert "YYYY-MM-DD" in response.json()["detail"]
