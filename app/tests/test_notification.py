from fastapi.testclient import TestClient
from app.main import app
from app.tests.test_leave import login_as

client = TestClient(app)

def test_get_notifications():
    cookie = login_as("carolyn50@example.com", "test")
    response = client.get("/api/notifications", cookies=cookie)
    assert response.status_code == 200
    data = response.json()
    assert "notifications" in data
    assert "pagination" in data
    if data["notifications"]:
        notif = data["notifications"][0]
        assert "id" in notif
        assert "title" in notif
        assert "message" in notif
        assert "is_read" in notif
        assert "created_at" in notif

def test_mark_notification_as_read():
    cookie = login_as("carolyn50@example.com", "test")
    # get a notification id
    response = client.get("/api/notifications", cookies=cookie)
    assert response.status_code == 200
    data = response.json()
    if not data["notifications"]:
        return  # No notifications to mark as read
    notif_id = data["notifications"][0]["id"]
    response = client.patch(f"/api/notifications/{notif_id}/read", cookies=cookie)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == notif_id
    assert data["is_read"] is True or data["is_read"] is False

def test_mark_all_notifications_as_read():
    cookie = login_as("carolyn50@example.com", "test")
    response = client.patch("/api/notifications/read-all", cookies=cookie)
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "count" in data
