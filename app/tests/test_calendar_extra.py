from fastapi.testclient import TestClient
from app.main import app
from app.tests.test_leave import login_as

client = TestClient(app)

def test_calendar_team_no_params():
    cookie = login_as("jessicavalentine@example.org", "test")
    response = client.get("/api/calendar/team", cookies=cookie)
    assert response.status_code == 200
    data = response.json()
    assert "days" in data

def test_calendar_team_only_year():
    cookie = login_as("jessicavalentine@example.org", "test")
    response = client.get("/api/calendar/team?year=2025", cookies=cookie)
    assert response.status_code == 200
    data = response.json()
    assert "days" in data

def test_calendar_team_only_month():
    cookie = login_as("jessicavalentine@example.org", "test")
    response = client.get("/api/calendar/team?month=5", cookies=cookie)
    assert response.status_code == 200
    data = response.json()
    assert "days" in data

def test_calendar_team_invalid_month():
    cookie = login_as("jessicavalentine@example.org", "test")
    response = client.get("/api/calendar/team?month=13", cookies=cookie)
    assert response.status_code == 400