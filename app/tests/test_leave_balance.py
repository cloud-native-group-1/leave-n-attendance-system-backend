from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def login_as(username: str, password: str):
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    # 取得 cookie
    cookies = response.cookies
    return cookies

def test_read_my_leave_balance():
    # login as subordinate (user id: 17)
    cookie = login_as("carolyn50@example.com", "test")
    response = client.get("/api/leave-balances", cookies=cookie)
    assert response.status_code == 200
    data = response.json()
    assert "year" in data
    assert isinstance(data["balances"], list)
    for balance in data["balances"]:
        assert "leave_type" in balance
        assert "quota" in balance
        assert "used_days" in balance
        assert "remaining_days" in balance
        assert "leave_requests" in balance

def test_read_user_leave_balance():
    # login as manager (user id: 19)
    cookie = login_as("jessicavalentine@example.org", "test")
    response = client.get("/api/leave-balances/17", cookies=cookie)
    assert response.status_code == 200
    data = response.json()
    assert "year" in data
    assert isinstance(data["balances"], list)
    for balance in data["balances"]:
        assert "leave_type" in balance
        assert "quota" in balance
        assert "used_days" in balance
        assert "remaining_days" in balance
        assert "leave_requests" in balance
