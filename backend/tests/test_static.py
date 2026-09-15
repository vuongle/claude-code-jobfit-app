"""Integration tests for serving the exported frontend."""

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture()
def static_client(tmp_path, monkeypatch):
    frontend = tmp_path / "out"
    frontend.mkdir()
    (frontend / "index.html").write_text("<html>index</html>")
    (frontend / "app.html").write_text("<html>app</html>")
    (frontend / "app.txt").write_text("rsc payload")
    (frontend / "404.html").write_text("<html>404</html>")
    (frontend / "_next").mkdir()
    (frontend / "_next" / "asset.js").write_text("js")
    monkeypatch.setenv("JOBFIT_DB_PATH", str(tmp_path / "jobfit.sqlite3"))
    monkeypatch.setenv("JOBFIT_FRONTEND_DIR", str(frontend))
    return TestClient(create_app())


def test_serves_built_pages(static_client):
    assert static_client.get("/").status_code == 200
    assert "index" in static_client.get("/").text
    assert static_client.get("/app").status_code == 200
    assert "app" in static_client.get("/app").text


def test_serves_next_assets(static_client):
    response = static_client.get("/_next/asset.js")
    assert response.status_code == 200


def test_serves_rsc_payloads(static_client):
    response = static_client.get("/app.txt")
    assert response.status_code == 200
    assert response.text == "rsc payload"


def test_unknown_path_gets_built_404_page(static_client):
    response = static_client.get("/nope")
    assert response.status_code == 404
    assert "404" in response.text


def test_unknown_path_cannot_escape_frontend_dir(static_client):
    response = static_client.get("/..%2F..%2Fetc%2Fpasswd")
    assert response.status_code == 404