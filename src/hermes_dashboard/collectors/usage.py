"""Usage collector — token usage, costs, and stats from state.db sessions."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Any

from hermes_dashboard.config import settings


def _connect(db_path) -> sqlite3.Connection | None:
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        return conn
    except (sqlite3.Error, OSError):
        return None


def get_usage_summary(
    agent_id: str = "",
    date_from: str = "",
    date_to: str = "",
    provider: str = "",
    model: str = "",
) -> dict[str, Any]:
    agents = settings.get_agents_for_query(agent_id)
    all_sessions: list[dict] = []

    for ag in agents:
        if not ag.state_db.exists():
            continue
        conn = _connect(ag.state_db)
        if not conn:
            continue

        where_clauses = ["1=1"]
        params: list = []

        if date_from:
            try:
                ts_from = datetime.fromisoformat(date_from.replace("Z", "+00:00")).timestamp()
                where_clauses.append("started_at >= ?")
                params.append(ts_from)
            except (ValueError, AttributeError):
                pass

        if date_to:
            try:
                ts_to = datetime.fromisoformat(date_to.replace("Z", "+00:00")).timestamp()
                where_clauses.append("started_at <= ?")
                params.append(ts_to)
            except (ValueError, AttributeError):
                pass

        if provider:
            where_clauses.append("billing_provider = ?")
            params.append(provider)

        if model:
            where_clauses.append("model = ?")
            params.append(model)

        where = " AND ".join(where_clauses)

        query = f"""
            SELECT id, model, billing_provider, billing_base_url,
                started_at, ended_at, message_count, tool_call_count,
                input_tokens, output_tokens, cache_read_tokens,
                cache_write_tokens, reasoning_tokens,
                estimated_cost_usd, actual_cost_usd, source
            FROM sessions
            WHERE {where}
            ORDER BY started_at DESC
        """

        try:
            rows = conn.execute(query, params).fetchall()
            for row in rows:
                d = dict(row)
                d["agent_id"] = ag.id
                d["agent_name"] = ag.name
                all_sessions.append(d)
        except sqlite3.Error:
            pass
        finally:
            conn.close()

    all_sessions.sort(key=lambda s: s.get("started_at") or 0, reverse=True)

    # Collect distinct providers and models for dropdowns (unfiltered)
    all_providers: set[str] = set()
    all_models: set[str] = set()
    for ag in agents:
        if not ag.state_db.exists():
            continue
        conn = _connect(ag.state_db)
        if not conn:
            continue
        try:
            for row in conn.execute("SELECT DISTINCT billing_provider FROM sessions WHERE billing_provider IS NOT NULL AND billing_provider != ''").fetchall():
                all_providers.add(row[0])
            for row in conn.execute("SELECT DISTINCT model FROM sessions WHERE model IS NOT NULL AND model != ''").fetchall():
                all_models.add(row[0])
        except sqlite3.Error:
            pass
        finally:
            conn.close()

    # Calendar
    calendar_agg: dict[str, dict] = {}
    for s in all_sessions:
        ts = s.get("started_at")
        if not ts:
            continue
        day = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
        if day not in calendar_agg:
            calendar_agg[day] = {"date": day, "sessions": 0, "input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "estimated_cost_usd": 0.0}
        a = calendar_agg[day]
        a["sessions"] += 1
        a["input_tokens"] += s.get("input_tokens") or 0
        a["output_tokens"] += s.get("output_tokens") or 0
        a["total_tokens"] += (s.get("input_tokens") or 0) + (s.get("output_tokens") or 0)
        a["estimated_cost_usd"] += s.get("estimated_cost_usd") or 0.0

    # Top sessions
    top = sorted(all_sessions, key=lambda s: (s.get("input_tokens") or 0) + (s.get("output_tokens") or 0), reverse=True)[:20]

    total_in = sum(s.get("input_tokens") or 0 for s in all_sessions)
    total_out = sum(s.get("output_tokens") or 0 for s in all_sessions)
    total_cost = sum(s.get("estimated_cost_usd") or 0.0 for s in all_sessions)

    return {
        "totals": {
            "sessions": len(all_sessions),
            "input_tokens": total_in,
            "output_tokens": total_out,
            "total_tokens": total_in + total_out,
            "estimated_cost_usd": round(total_cost, 4),
            "tool_calls": sum(s.get("tool_call_count") or 0 for s in all_sessions),
            "messages": sum(s.get("message_count") or 0 for s in all_sessions),
        },
        "providers": sorted(all_providers),
        "models": sorted(all_models),
        "calendar": sorted(calendar_agg.values(), key=lambda x: x["date"], reverse=True),
        "top_sessions": [{
            "id": s["id"], "agent_name": s.get("agent_name", ""),
            "model": s.get("model"), "provider": s.get("billing_provider"),
            "started_at": s.get("started_at"),
            "input_tokens": s.get("input_tokens") or 0,
            "output_tokens": s.get("output_tokens") or 0,
            "total_tokens": (s.get("input_tokens") or 0) + (s.get("output_tokens") or 0),
            "tool_calls": s.get("tool_call_count") or 0,
            "messages": s.get("message_count") or 0,
            "estimated_cost_usd": s.get("estimated_cost_usd") or 0.0,
        } for s in top],
    }
