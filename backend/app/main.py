"""FastAPI application for JobFit: fake session, PDF upload, health probe.

Also serves the statically exported Next.js frontend from the same process,
so the whole app answers on one port.
"""

import os

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import db
from .extract import ExtractionError, extract_pdf_text


class SessionResponse(BaseModel):
    user_id: int
    name: str


class UploadResponse(BaseModel):
    id: int
    filename: str
    cv_text: str


class HealthResponse(BaseModel):
    status: str


def create_app() -> FastAPI:
    app = FastAPI(title="JobFit", version="0.1.0")
    db.init_db()

    @app.get("/api/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(status="ok")

    @app.post("/api/session", response_model=SessionResponse)
    def create_session(name: str = Form(...)) -> SessionResponse:
        if not name.strip():
            raise HTTPException(status_code=422, detail="Name is required.")
        conn = db.connect()
        try:
            user_id = db.create_user(conn, name.strip())
        finally:
            conn.close()
        return SessionResponse(user_id=user_id, name=name.strip())

    @app.post("/api/uploads", response_model=UploadResponse)
    def create_upload(
        user_id: int = Form(...),
        jd_text: str = Form(...),
        cv_file: UploadFile = File(...),
    ) -> UploadResponse:
        if not jd_text.strip():
            raise HTTPException(status_code=422, detail="Job description is required.")
        conn = db.connect()
        try:
            if conn.execute("SELECT 1 FROM users WHERE id = ?", (user_id,)).fetchone() is None:
                raise HTTPException(status_code=404, detail="Unknown user.")
            data = cv_file.file.read()
            if not data.startswith(b"%PDF-"):
                raise HTTPException(status_code=422, detail="CV must be a PDF file.")
            try:
                cv_text = extract_pdf_text(data)
            except ExtractionError as exc:
                raise HTTPException(status_code=422, detail=str(exc)) from exc
            if not cv_text.strip():
                raise HTTPException(status_code=422, detail="No text could be extracted from the PDF.")
            filename = cv_file.filename or "cv.pdf"
            upload_id = db.create_upload(conn, user_id, filename, jd_text, cv_text)
        finally:
            conn.close()
        return UploadResponse(id=upload_id, filename=filename, cv_text=cv_text)

    _mount_frontend(app)
    return app


def _mount_frontend(app: FastAPI) -> None:
    """Serve the statically exported Next.js build if it is present."""
    frontend_dir = os.environ.get("JOBFIT_FRONTEND_DIR", "/app/frontend_out")
    if not os.path.isdir(frontend_dir):
        return
    assets = os.path.join(frontend_dir, "_next")
    if os.path.isdir(assets):
        app.mount("/_next", StaticFiles(directory=assets), name="next-assets")

    def page(filename: str):
        def handler() -> FileResponse:
            return FileResponse(os.path.join(frontend_dir, filename))

        return handler

    app.get("/", include_in_schema=False)(page("index.html"))
    app.get("/app", include_in_schema=False)(page("app.html"))

    def static_file(full_path: str) -> FileResponse:
        candidate = os.path.normpath(os.path.join(frontend_dir, full_path))
        if candidate.startswith(os.path.abspath(frontend_dir)) and os.path.isfile(candidate):
            return FileResponse(candidate)
        return FileResponse(
            os.path.join(frontend_dir, "404.html"), status_code=404
        )

    app.get("/{full_path:path}", include_in_schema=False)(static_file)