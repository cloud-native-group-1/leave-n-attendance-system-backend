from fastapi.testclient import TestClient
from app.main import app
from app.schemas.leave import LeaveTypeBasic, ProxyUserOut

client = TestClient(app)

def login_as(username: str, password: str):
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    # 取得 cookie
    cookies = response.cookies
    return cookies

def test_create_leave_request():
    # login as subordinate (user id: 17)
    cookie = login_as("carolyn50@example.com", "test")

    response = client.post("/api/leave-requests", json={
        "leave_type_id": 5,
        "start_date": "2024-12-01",
        "end_date": "2024-12-03",
        "reason": "Unit test",
        "proxy_user_id": 21 
    }, cookies=cookie)

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert "request_id" in data
    assert "leave_type" in data
    assert "start_date" in data
    assert "end_date" in data
    assert isinstance(data["reason"], str) 
    assert data["status"] == "pending"
    assert data["days_count"] == 2 
    assert "proxy_person" in data

def test_list_my_leave_requests():
    # login as subordinate (user id: 17)
    cookie = login_as("carolyn50@example.com", "test")
    # test with all query parameter
    response = client.get("/api/leave-requests?status=pending&start_date=2024-12-01&end_date=2024-12-10&page=1&per_page=10", cookies=cookie)
    assert response.status_code == 200
    data = response.json()
    assert "leave_requests" in data
    assert isinstance(data["leave_requests"], list)
    assert "pagination" in data

    # test without any query parameter
    response = client.get("/api/leave-requests", cookies=cookie)
    assert response.status_code == 200
    data = response.json()
    assert "leave_requests" in data
    assert isinstance(data["leave_requests"], list)
    assert "pagination" in data

def test_list_team_leave_requests():
    # login as manager (user id: 19)
    cookie = login_as("jessicavalentine@example.org", "test")    
    # test without any query parameter
    response = client.get("/api/leave-requests/team", cookies=cookie)
    assert response.status_code == 200
    data = response.json()
    assert "leave_requests" in data
    assert isinstance(data["leave_requests"], list)
    assert "pagination" in data
    assert "user" in data["leave_requests"][0]
    
    # test with all query parameter
    response = client.get("/api/leave-requests/team?status=pending&start_date=2024-12-01&end_date=2024-12-10&page=1&per_page=10", cookies=cookie)
    assert response.status_code == 200
    data = response.json()
    assert "leave_requests" in data
    assert isinstance(data["leave_requests"], list)
    assert "pagination" in data


def test_list_pending_leave_requests():
    # login as manager (user id: 19)
    cookie = login_as("jessicavalentine@example.org", "test")    
    # test without any query parameter
    response = client.get("/api/leave-requests/pending", cookies=cookie)
    assert response.status_code == 200
    data = response.json()
    assert "leave_requests" in data
    assert isinstance(data["leave_requests"], list)
    assert "pagination" in data

    # test with all query parameter
    response = client.get("/api/leave-requests/pending?start_date=2024-12-01&end_date=2024-12-10&page=1&per_page=10", cookies=cookie)
    assert response.status_code == 200
    data = response.json()
    assert "leave_requests" in data
    assert isinstance(data["leave_requests"], list)
    assert "pagination" in data