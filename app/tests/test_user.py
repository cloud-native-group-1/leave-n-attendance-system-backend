from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def login_as(username: str, password: str):
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    # 取得 cookie
    cookies = response.cookies
    return cookies

def test_get_my_profile():
    # login as manager (user id: 19)
    cookie = login_as("jessicavalentine@example.org", "test")
    response = client.get("/api/users/me", cookies=cookie)
    assert response.status_code == 200
    assert response.json() == {
        "id": 19,
        "employee_id": "EMP166",
        "first_name": "Scott",
        "last_name": "Burton",
        "email": "jessicavalentine@example.org",
        "department": {
            "id": 6,
            "name": "Scott, Castillo and Mccann"
        },
        "position": "Hydrogeologist",
        "is_manager": True,
        "manager": None,
        "hire_date": "2023-02-04"
    }
    # login as subordinate (user id: 17)
    cookie = login_as("carolyn50@example.com", "test")
    response = client.get("/api/users/me", cookies=cookie)
    assert response.status_code == 200
    assert response.json() == {
        "id": 17,
        "employee_id": "EMP148",
        "first_name": "Evelyn",
        "last_name": "Ware",
        "email": "carolyn50@example.com",
        "department": {
            "id": 6,
            "name": "Scott, Castillo and Mccann"
        },
        "position": "Press photographer",
        "is_manager": False,
        "manager": {
            "id": 19,
            "first_name": "Scott",
            "last_name": "Burton"
        },
        "hire_date": "2023-07-16"
    }


def test_get_teammate():
    # login as subordinate (user id: 17)
    cookie = login_as("carolyn50@example.com", "test")
    response = client.get("/api/users/team", cookies=cookie)
    assert response.status_code == 200
    assert response.json() == {
        "team_members": [
            {
            "id": 17,
            "employee_id": "EMP148",
            "first_name": "Evelyn",
            "last_name": "Ware",
            "position": "Press photographer",
            "email": "carolyn50@example.com",
            "department": {
                "id": 6,
                "name": "Scott, Castillo and Mccann"
            }
            },
            {
            "id": 21,
            "employee_id": "EMP25859",
            "first_name": "Virginia",
            "last_name": "Rodriguez",
            "position": "Water quality scientist",
            "email": "coxlaurie@example.com",
            "department": {
                "id": 10,
                "name": "Hurley, Marshall and Rodgers"
            }
            }
        ]
    }

def test_get_subordinates():
    # login as manager (user id: 19)
    cookie = login_as("jessicavalentine@example.org", "test")
    response = client.get("/api/users/subordinates", cookies=cookie)
    assert response.status_code == 200
    assert response.json() == {
        "team_members": [
            {
            "id": 17,
            "employee_id": "EMP148",
            "first_name": "Evelyn",
            "last_name": "Ware",
            "position": "Press photographer",
            "email": "carolyn50@example.com",
            "department": {
                "id": 6,
                "name": "Scott, Castillo and Mccann"
            }
            },
            {
            "id": 21,
            "employee_id": "EMP25859",
            "first_name": "Virginia",
            "last_name": "Rodriguez",
            "position": "Water quality scientist",
            "email": "coxlaurie@example.com",
            "department": {
                "id": 10,
                "name": "Hurley, Marshall and Rodgers"
            }
            }
        ]
    }
    # login as subordinate (user id: 17)
    cookie = login_as("carolyn50@example.com", "test")
    response = client.get("/api/users/subordinates", cookies=cookie)
    assert response.status_code == 403 

def test_get_user_by_id():
    # login as manager (user id: 19)
    cookie = login_as("jessicavalentine@example.org", "test")
    response = client.get("/api/users/17", cookies=cookie)
    assert response.status_code == 200
    assert response.json() == {
        "id": 17,
        "employee_id": "EMP148",
        "first_name": "Evelyn",
        "last_name": "Ware",
        "email": "carolyn50@example.com",
        "department": {
            "id": 6,
            "name": "Scott, Castillo and Mccann"
        },
        "position": "Press photographer",
        "is_manager": False,
        "manager": {
            "id": 19,
            "first_name": "Scott",
            "last_name": "Burton"
        },
        "hire_date": "2023-07-16"
    }