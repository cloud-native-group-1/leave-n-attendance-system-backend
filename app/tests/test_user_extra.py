from fastapi.testclient import TestClient
from app.main import app
from app.tests.test_leave import login_as

client = TestClient(app)

def test_get_user_by_invalid_id():
    cookie = login_as("carolyn50@example.com", "test")
    response = client.get("/api/users/99999", cookies=cookie)
    assert response.status_code == 404

def test_get_subordinates_as_non_manager():
    cookie = login_as("carolyn50@example.com", "test")
    response = client.get("/api/users/subordinates", cookies=cookie)
    assert response.status_code == 403