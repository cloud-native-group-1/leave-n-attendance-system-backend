from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_login_invalid_credentials():
    response = client.post("/api/auth/login", json={"username": "notexist@example.com", "password": "wrong"})
    assert response.status_code == 401