"""Shared fixtures: an app bound to a throwaway SQLite database."""

import os
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.main import create_app  # noqa: E402

FIXTURE_PDF = os.path.join(
    os.path.dirname(__file__), "..", "..", "fixtures", "case-02-marketing-partial", "cv.pdf"
)


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("JOBFIT_DB_PATH", str(tmp_path / "jobfit.sqlite3"))
    return TestClient(create_app())


@pytest.fixture()
def user_id(client):
    response = client.post("/api/session", data={"name": "Test User"})
    return response.json()["user_id"]


@pytest.fixture()
def fixture_pdf_bytes():
    with open(FIXTURE_PDF, "rb") as fh:
        return fh.read()