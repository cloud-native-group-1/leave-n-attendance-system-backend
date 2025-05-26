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
        "leave_type_id": 101,
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

def test_get_leave_request_detail():
    # login as subordinate (user id: 17)
    cookie = login_as("carolyn50@example.com", "test")
    # create a leave request to get its id
    response = client.post("/api/leave-requests", json={
        "leave_type_id": 101,
        "start_date": "2024-12-01",
        "end_date": "2024-12-03",
        "reason": "Unit test detail",
        "proxy_user_id": 21
    }, cookies=cookie)
    assert response.status_code == 201
    leave_id = response.json()["id"]
    # get leave request detail
    response = client.get(f"/api/leave-requests/{leave_id}", cookies=cookie)
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "request_id" in data
    assert "user" in data
    assert "leave_type" in data
    assert "start_date" in data
    assert "end_date" in data
    assert "days_count" in data
    assert "reason" in data
    assert "status" in data
    assert "created_at" in data

def test_approve_and_reject_leave_request():
    # login as subordinate to create a leave request
    cookie_sub = login_as("carolyn50@example.com", "test")
    response = client.post("/api/leave-requests", json={
        "leave_type_id": 101,
        "start_date": "2024-12-05",
        "end_date": "2024-12-06",
        "reason": "Unit test approve/reject",
        "proxy_user_id": 21
    }, cookies=cookie_sub)
    assert response.status_code == 201
    leave_id = response.json()["id"]
    # login as manager to approve
    cookie_mgr = login_as("jessicavalentine@example.org", "test")
    response = client.patch(f"/api/leave-requests/{leave_id}/approve", cookies=cookie_mgr)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "approved"
    assert "approver" in data
    assert "approved_at" in data
    # Now create another leave request for rejection
    response = client.post("/api/leave-requests", json={
        "leave_type_id": 101,
        "start_date": "2024-12-09",
        "end_date": "2024-12-10",
        "reason": "Unit test reject",
        "proxy_user_id": 21
    }, cookies=cookie_sub)
    assert response.status_code == 201
    leave_id = response.json()["id"]
    # manager rejects
    response = client.patch(f"/api/leave-requests/{leave_id}/reject", json={"rejection_reason": "Not allowed for test"}, cookies=cookie_mgr)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "rejected"
    assert "approver" in data
    assert "approved_at" in data
    assert "rejection_reason" in data

def test_request_leave_invalid_leave_type():
    cookie = login_as("carolyn50@example.com", "test")
    response = client.post("/api/leave-requests", json={
        "leave_type_id": 99999,
        "start_date": "2025-12-01",
        "end_date": "2025-12-03",
        "reason": "Invalid leave type",
        "proxy_user_id": 21
    }, cookies=cookie)
    assert response.status_code == 400

def test_request_leave_invalid_proxy():
    cookie = login_as("carolyn50@example.com", "test")
    response = client.post("/api/leave-requests", json={
        "leave_type_id": 5,
        "start_date": "2025-12-01",
        "end_date": "2025-12-03",
        "reason": "Invalid proxy",
        "proxy_user_id": 99999
    }, cookies=cookie)
    assert response.status_code == 400

def test_list_my_leave_requests_invalid_status():
    cookie = login_as("carolyn50@example.com", "test")
    response = client.get("/api/leave-requests?status=notastatus", cookies=cookie)
    assert response.status_code == 200

def test_list_my_leave_requests_invalid_page():
    cookie = login_as("carolyn50@example.com", "test")
    response = client.get("/api/leave-requests?page=-1", cookies=cookie)
    assert response.status_code == 422

def test_list_team_leave_requests_non_manager():
    cookie = login_as("carolyn50@example.com", "test")
    response = client.get("/api/leave-requests/team", cookies=cookie)
    assert response.status_code == 200
    data = response.json()
    assert data["pagination"]["total"] == 0

def test_list_team_leave_requests_invalid_user():
    cookie = login_as("jessicavalentine@example.org", "test")
    response = client.get("/api/leave-requests/team?user_id=99999", cookies=cookie)
    assert response.status_code == 200
    data = response.json()
    assert data["pagination"]["total"] == 0

def test_list_pending_leave_requests_non_manager():
    cookie = login_as("carolyn50@example.com", "test")
    response = client.get("/api/leave-requests/pending", cookies=cookie)
    assert response.status_code == 403

def test_get_leave_request_details_not_found():
    cookie = login_as("carolyn50@example.com", "test")
    response = client.get("/api/leave-requests/999999", cookies=cookie)
    assert response.status_code in (404, 500)

def test_approve_leave_request_permission():
    cookie = login_as("carolyn50@example.com", "test")  # Not a manager
    response = client.patch("/api/leave-requests/1/approve", cookies=cookie)
    assert response.status_code in (403, 400, 404)

def test_reject_leave_request_permission():
    cookie = login_as("carolyn50@example.com", "test")  # Not a manager
    response = client.patch("/api/leave-requests/1/reject", json={"rejection_reason": "No"}, cookies=cookie)
    assert response.status_code in (403, 400, 404, 500)

def test_reject_leave_request_not_found():
    cookie = login_as("jessicavalentine@example.org", "test")
    response = client.patch("/api/leave-requests/999999/reject", json={"rejection_reason": "No"}, cookies=cookie)
    assert response.status_code in (404, 500)

def test_approve_leave_request_not_found():
    cookie = login_as("jessicavalentine@example.org", "test")
    response = client.patch("/api/leave-requests/999999/approve", cookies=cookie)
    assert response.status_code in (404, 500)