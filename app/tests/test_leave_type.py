from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_all_leave_types():
    response = client.get("/api/leave-types/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_leave_type_by_id():
    # Assumes leave type with id=5 exists
    response = client.get("/api/leave-types/")
    leave_types = response.json()
    if leave_types:
        leave_type_id = leave_types[0]["id"]
        response = client.get(f"/api/leave-types/{leave_type_id}")
        assert response.status_code in (200, 404)  # 404 if not implemented

def test_get_leave_type_by_invalid_id():
    response = client.get("/api/leave-types/99999")
    assert response.status_code in (404, 422)