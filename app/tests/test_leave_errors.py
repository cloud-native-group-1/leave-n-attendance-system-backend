from fastapi.testclient import TestClient
from app.main import app
from app.tests.test_leave import login_as

client = TestClient(app)

def test_create_leave_request_invalid_type():
    cookie = login_as("carolyn50@example.com", "test")
    response = client.post("/api/leave-requests", json={
        "leave_type_id": 99999,
        "start_date": "2025-12-01",
        "end_date": "2025-12-03",
        "reason": "Invalid type",
        "proxy_user_id": 21
    }, cookies=cookie)
    assert response.status_code == 400

def test_create_leave_request_invalid_proxy():
    cookie = login_as("carolyn50@example.com", "test")
    response = client.post("/api/leave-requests", json={
        "leave_type_id": 5,
        "start_date": "2025-12-01",
        "end_date": "2025-12-03",
        "reason": "Invalid proxy",
        "proxy_user_id": 99999
    }, cookies=cookie)
    assert response.status_code == 400

def test_approve_leave_request_invalid_permission():
    cookie_mgr = login_as("carolyn50@example.com", "test")  # Not a manager
    response = client.patch("/api/leave-requests/1/approve", cookies=cookie_mgr)
    assert response.status_code in (403, 400, 404)