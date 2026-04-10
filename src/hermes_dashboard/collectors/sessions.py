"""Sessions collector — reads from ~/.hermes/sessions/ and state.db."""

from __future__ import annotations

import json
import sqlite3

from hermes_dashboard.config import settings
from hermes_dashboard.schemas import SessionDetail, SessionSummary


def list_sessions(limit: int = 50, offset: int = 0) -> list[SessionSummary]:
    """List sessions from the sessions directory, sorted by modification time."""
    sessions_dir = settings.sessions_dir
    if not sessions_dir.exists():
        return []

    files = sorted(
        sessions_dir.glob("*.json"),
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )

    results = []
    for f in files[offset : offset + limit]:
        if f.name.startswith("sessions.json"):
            continue
        stat = f.stat()
        # Try to extract session metadata
        session_id = f.stem
        started_at = None
        channel = None
        msg_count = 0
        try:
            data = json.loads(f.read_text())
            if isinstance(data, dict):
                started_at = data.get("started_at") or data.get("created_at")
                channel = data.get("channel")
                msgs = data.get("messages", [])
                msg_count = len(msgs) if isinstance(msgs, list) else 0
                session_id = data.get("session_id", session_id)
            elif isinstance(data, list):
                msg_count = len(data)
        except (json.JSONDecodeError, OSError):
            pass

        results.append(
            SessionSummary(
                id=session_id,
                started_at=started_at,
                channel=channel,
                message_count=msg_count,
                file_size=stat.st_size,
            )
        )

    return results


def get_session(session_id: str) -> SessionDetail | None:
    """Load full session transcript."""
    sessions_dir = settings.sessions_dir
    # Try exact match first
    for pattern in (f"{session_id}.json", f"session_{session_id}*.json"):
        matches = list(sessions_dir.glob(pattern))
        if matches:
            f = matches[0]
            try:
                data = json.loads(f.read_text())
                if isinstance(data, dict):
                    return SessionDetail(
                        id=data.get("session_id", session_id),
                        messages=data.get("messages", []),
                    )
                elif isinstance(data, list):
                    return SessionDetail(id=session_id, messages=data)
            except (json.JSONDecodeError, OSError):
                pass

    # Try state.db
    if settings.state_db.exists():
        try:
            conn = sqlite3.connect(str(settings.state_db))
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT role, content, timestamp FROM messages WHERE session_id = ? ORDER BY rowid",
                (session_id,),
            ).fetchall()
            conn.close()
            if rows:
                return SessionDetail(
                    id=session_id,
                    messages=[dict(r) for r in rows],
                )
        except sqlite3.Error:
            pass

    return None


def search_sessions(query: str, limit: int = 20) -> list[dict]:
    """Full-text search across messages using SQLite FTS."""
    if not settings.state_db.exists():
        return []

    try:
        conn = sqlite3.connect(str(settings.state_db))
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT m.session_id, m.role, m.content, m.timestamp "
            "FROM messages_fts fts "
            "JOIN messages m ON m.id = fts.rowid "
            "WHERE messages_fts MATCH ? "
            "ORDER BY rank LIMIT ?",
            (query, limit),
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except sqlite3.Error:
        return []
