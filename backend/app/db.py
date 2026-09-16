"""SQLite access for JobFit.

Early tickets recreate the schema on every boot; once real accounts land the
data has to survive restarts instead.
"""

import os
import sqlite3

SCHEMA = """
DROP TABLE IF EXISTS scores;
DROP TABLE IF EXISTS uploads;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE uploads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    filename TEXT NOT NULL,
    jd_text TEXT NOT NULL,
    cv_text TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    upload_id INTEGER NOT NULL REFERENCES uploads(id),
    overall_score INTEGER NOT NULL,
    result TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


def db_path() -> str:
    return os.environ.get("JOBFIT_DB_PATH", "/data/jobfit.sqlite3")


def connect(path: str | None = None) -> sqlite3.Connection:
    conn = sqlite3.connect(path or db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(path: str | None = None) -> None:
    target = path or db_path()
    directory = os.path.dirname(target)
    if directory:
        os.makedirs(directory, exist_ok=True)
    conn = connect(target)
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()


def create_user(conn: sqlite3.Connection, name: str) -> int:
    cur = conn.execute("INSERT INTO users (name) VALUES (?)", (name,))
    conn.commit()
    return cur.lastrowid


def create_upload(
    conn: sqlite3.Connection,
    user_id: int,
    filename: str,
    jd_text: str,
    cv_text: str,
) -> int:
    cur = conn.execute(
        "INSERT INTO uploads (user_id, filename, jd_text, cv_text) VALUES (?, ?, ?, ?)",
        (user_id, filename, jd_text, cv_text),
    )
    conn.commit()
    return cur.lastrowid


def get_upload(conn: sqlite3.Connection, upload_id: int) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM uploads WHERE id = ?", (upload_id,)).fetchone()


def create_score(
    conn: sqlite3.Connection,
    upload_id: int,
    overall_score: int,
    result_json: str,
) -> int:
    cur = conn.execute(
        "INSERT INTO scores (upload_id, overall_score, result) VALUES (?, ?, ?)",
        (upload_id, overall_score, result_json),
    )
    conn.commit()
    return cur.lastrowid