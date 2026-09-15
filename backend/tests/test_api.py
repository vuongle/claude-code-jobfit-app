"""Integration tests for the API endpoints."""

from app.extract import extract_pdf_text


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_session_creates_user(client):
    response = client.post("/api/session", data={"name": "Dana"})
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Dana"
    assert isinstance(body["user_id"], int)


def test_session_rejects_blank_name(client):
    response = client.post("/api/session", data={"name": "   "})
    assert response.status_code == 422


def test_upload_round_trip(client, user_id, fixture_pdf_bytes):
    response = client.post(
        "/api/uploads",
        data={"user_id": str(user_id), "jd_text": "Marketing manager role"},
        files={"cv_file": ("cv.pdf", fixture_pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["id"] > 0
    assert body["filename"] == "cv.pdf"
    assert body["cv_text"] == extract_pdf_text(fixture_pdf_bytes)


def test_upload_unknown_user_404(client, fixture_pdf_bytes):
    response = client.post(
        "/api/uploads",
        data={"user_id": "9999", "jd_text": "JD"},
        files={"cv_file": ("cv.pdf", fixture_pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Unknown user."


def test_upload_rejects_non_pdf(client, user_id):
    response = client.post(
        "/api/uploads",
        data={"user_id": str(user_id), "jd_text": "JD"},
        files={"cv_file": ("cv.txt", b"plain text", "text/plain")},
    )
    assert response.status_code == 422
    assert "PDF" in response.json()["detail"]


def test_upload_rejects_unreadable_pdf(client, user_id):
    response = client.post(
        "/api/uploads",
        data={"user_id": str(user_id), "jd_text": "JD"},
        files={"cv_file": ("cv.pdf", b"%PDF-1.4 garbage", "application/pdf")},
    )
    assert response.status_code == 422


def test_upload_rejects_blank_jd(client, user_id, fixture_pdf_bytes):
    response = client.post(
        "/api/uploads",
        data={"user_id": str(user_id), "jd_text": "   "},
        files={"cv_file": ("cv.pdf", fixture_pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 422