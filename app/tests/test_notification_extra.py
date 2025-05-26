from fastapi.testclient import TestClient
from app.main import app
from app.tests.test_leave import login_as

client = TestClient(app)

def test_get_notifications_unread_only():
    cookie = login_as("carolyn50@example.com", "test")
    response = client.get("/api/notifications?unread_only=true", cookies=cookie)
    assert response.status_code == 200
    assert "notifications" in response.json()

def test_mark_notification_as_read_invalid():
    cookie = login_as("carolyn50@example.com", "test")
    response = client.patch("/api/notifications/99999/read", cookies=cookie)
    assert response.status_code in (404, 400)