from fastapi.testclient import TestClient
from app.main import app
from app.tests.test_leave import login_as
import io

client = TestClient(app)

def test_upload_attachment_invalid_leave():
    cookie = login_as("carolyn50@example.com", "test")
    file_content = b"dummy content"
    files = {"file": ("test.txt", io.BytesIO(file_content), "text/plain")}
    response = client.post("/api/leave-requests/99999/attachments", files=files, cookies=cookie)
    assert response.status_code in (404, 403)

# Add more tests for valid upload if you have a valid leave_request_id

def test_get_attachments_for_leave_request():
    cookie = login_as("carolyn50@example.com", "test")
    response = client.get("/api/leave-requests/138/attachments", cookies=cookie)
    assert response.status_code == 200
    data = response.json()
    assert "attachments" in data
    assert "total_count" in data
    assert isinstance(data["attachments"], list)
