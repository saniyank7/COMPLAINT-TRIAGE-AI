import sqlite3
from contextlib import contextmanager

from app.config import env


SCHEMA = """
CREATE TABLE IF NOT EXISTS triage_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    text_len INTEGER,
    product TEXT,
    issue TEXT,
    summary TEXT,
    urgent INTEGER,
    urgency_reason TEXT,
    latency_ms INTEGER,
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    valid_json INTEGER,
    retried INTEGER,
    error TEXT
);

CREATE TABLE IF NOT EXISTS complaints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    complaint_text TEXT NOT NULL,
    product TEXT,
    issue TEXT,
    summary TEXT,
    urgent INTEGER,
    urgency_reason TEXT,
    latency_ms INTEGER
);
"""


@contextmanager
def connect():
    conn = sqlite3.connect(env("DB_PATH", "triage.db"))
    conn.row_factory = sqlite3.Row

    try:
        conn.executescript(SCHEMA)
        yield conn
        conn.commit()
    finally:
        conn.close()


def log_result(text_len: int, result, meta: dict) -> None:
    with connect() as conn:
        conn.execute(
            """INSERT INTO triage_results
               (text_len, product, issue, summary, urgent, urgency_reason,
                latency_ms, prompt_tokens, completion_tokens, valid_json, retried, error)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                text_len,
                result.product if result else None,
                result.issue if result else None,
                result.summary if result else None,
                int(result.urgent) if result else None,
                result.urgency_reason if result else None,
                meta["latency_ms"],
                meta["prompt_tokens"],
                meta["completion_tokens"],
                int(meta["valid_json"]),
                int(meta["retried"]),
                meta["error"],
            ),
        )

def save_complaint_for_dashboard(text: str, result, meta: dict) -> int:
    if result is None:
        return 0

    with connect() as conn:
        cursor = conn.execute(
            """INSERT INTO complaints
               (complaint_text, product, issue, summary,
                urgent, urgency_reason, latency_ms)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                text,
                result.product,
                result.issue,
                result.summary,
                int(result.urgent),
                result.urgency_reason,
                meta.get("latency_ms", 0),
            ),
        )

        return cursor.lastrowid
    
def get_complaints_for_dashboard() -> list:
    """
    Retrieve complaints and their AI analysis
    for the banker dashboard.
    """

    with connect() as conn:
        rows = conn.execute(
            """SELECT
                   id,
                   created_at,
                   complaint_text,
                   product,
                   issue,
                   summary,
                   urgent,
                   urgency_reason,
                   latency_ms
               FROM complaints
               ORDER BY id DESC"""
        ).fetchall()

        return [dict(row) for row in rows]


def stats() -> dict:
    with connect() as conn:
        row = conn.execute(
            """SELECT COUNT(*) AS n,
                      AVG(latency_ms) AS avg_latency_ms,
                      AVG(valid_json) AS first_try_valid_rate,
                      SUM(prompt_tokens + completion_tokens) AS total_tokens,
                      SUM(CASE WHEN product IS NULL THEN 1 ELSE 0 END) AS failures
               FROM triage_results"""
        ).fetchone()

        return dict(row)