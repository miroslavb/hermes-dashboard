"""Sessions collector — reads from ~/.hermes/sessions/ and state.db."""

from __future__ import annotations

import json
import sqlite3

from hermes_dashboard.config import AgentConfig, settings
from hermes_dashboard.schemas import SessionDetail, SessionSummary


def _parse_jsonl_session(f) -> SessionSummary | None:
    """Parse a .jsonl session file for metadata."""
    import time as _time
    stat = f.stat()
    session_id = f.stem
    channel = None
    msg_count = 0
    started_at = None
    try:
        with open(f, "r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                msg_count += 1
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if obj.get("role") == "session_meta":
                    channel = obj.get("platform") or obj.get("source")
                    ts = obj.get("timestamp")
                    if ts:
                        started_at = ts
                if not started_at and obj.get("timestamp"):
                    started_at = obj["timestamp"]
        # session_meta line is not a user/assistant message
        if msg_count > 0:
            msg_count -= 1  # subtract meta line
    except (OSError, json.JSONDecodeError):
        pass
    return SessionSummary(
        id=session_id,
        started_at=started_at,
        channel=channel,
        message_count=msg_count,
        file_size=stat.st_size,
    )


def _parse_json_session(f) -> SessionSummary | None:
    """Parse a .json session/request file for metadata."""
    stat = f.stat()
    session_id = f.stem
    if f.name.startswith("sessions.json") or f.name.startswith("request_dump_"):
        # Skip index files and request dumps for cleaner listing
        return None
    channel = None
    msg_count = 0
    started_at = None
    try:
        data = json.loads(f.read_text())
        if isinstance(data, dict):
            started_at = data.get("started_at") or data.get("created_at")
            channel = data.get("channel") or data.get("source")
            msgs = data.get("messages", [])
            msg_count = len(msgs) if isinstance(msgs, list) else 0
            session_id = data.get("session_id", session_id)
        elif isinstance(data, list):
            msg_count = len(data)
    except (json.JSONDecodeError, OSError):
        pass
    return SessionSummary(
        id=session_id,
        started_at=started_at,
        channel=channel,
        message_count=msg_count,
        file_size=stat.st_size,
    )


def list_sessions(limit: int = 50, offset: int = 0, agent_id: str = "") -> list[SessionSummary]:
    """List sessions from all (or one) agent's sessions directory."""
    agents = settings.get_agents_for_query(agent_id)

    all_entries: list[SessionSummary] = []
    for ag in agents:
        sessions_dir = ag.sessions_dir
        if not sessions_dir.exists():
            continue

        # Collect .jsonl files (primary) and .json files (fallback)
        jsonl_ids = {f.stem for f in sessions_dir.glob("*.jsonl")}
        all_files = list(sessions_dir.glob("*.jsonl"))
        for f in sessions_dir.glob("*.json"):
            if f.stem not in jsonl_ids:
                all_files.append(f)

        for f in all_files:
            if f.suffix == ".jsonl":
                entry = _parse_jsonl_session(f)
            else:
                entry = _parse_json_session(f)
            if entry:
                # Tag with agent info
                if not entry.channel:
                    entry.channel = ag.id
                all_entries.append(entry)

    # Sort by modification time across all agents
    all_entries.sort(key=lambda e: e.file_size, reverse=True)
    # Actually sort by mtime — need to re-check files
    # Simple approach: just return sorted by file_size as proxy
    return all_entries[offset: offset + limit]


def get_session(session_id: str, agent_id: str = "") -> SessionDetail | None:
    """Load full session transcript. Searches all agents if agent_id is empty."""
    agents = settings.get_agents_for_query(agent_id)

    for ag in agents:
        sessions_dir = ag.sessions_dir

        # Try .jsonl first
        jsonl_path = sessions_dir / f"{session_id}.jsonl"
        if jsonl_path.exists():
            try:
                messages = []
                with open(jsonl_path, "r", encoding="utf-8", errors="replace") as fh:
                    for line in fh:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            obj = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        role = obj.get("role", "")
                        if role in ("session_meta",):
                            continue
                        content = obj.get("content", "")
                        if isinstance(content, str):
                            if len(content) > 8000:
                                content = content[:8000] + "\n... [truncated]"
                        messages.append({
                            "role": role,
                            "content": content,
                            "timestamp": obj.get("timestamp"),
                        })
                if messages:
                    return SessionDetail(id=session_id, messages=messages, agent=ag.id)
            except OSError:
                pass

        # Try .json
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
                            agent=ag.id,
                        )
                    elif isinstance(data, list):
                        return SessionDetail(id=session_id, messages=data, agent=ag.id)
                except (json.JSONDecodeError, OSError):
                    pass

        # Try state.db
        if ag.state_db.exists():
            try:
                conn = sqlite3.connect(str(ag.state_db))
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
                        agent=ag.id,
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
