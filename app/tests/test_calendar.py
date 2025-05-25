from fastapi.testclient import TestClient
from app.main import app
from app.tests.test_leave import login_as

client = TestClient(app)

def test_get_team_calendar():
    # login as manager (user id: 19)
    cookie = login_as("jessicavalentine@example.org", "test")
    response = client.get("/api/calendar/team?year=2024&month=12", cookies=cookie)
    assert response.status_code == 200
    data = response.json()
    assert "year" in data
    assert "month" in data
    assert "days" in data
    assert isinstance(data["days"], list)
    if data["days"]:
        day = data["days"][0]
        assert "date" in day
        assert "members_on_leave" in day
        assert isinstance(day["members_on_leave"], list)
