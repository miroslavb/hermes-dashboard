"""Agents API — list available agents."""

from __future__ import annotations

from fastapi import APIRouter

from hermes_dashboard.config import settings

router = APIRouter()


@router.get("")
async def list_agents():
    """List all discovered agents with basic stats."""
    result = []
    for ag in settings.agents:
        info = {
            "id": ag.id,
            "name": ag.name,
            "home": str(ag.home),
            "exists": ag.exists(),
        }
        # Quick stats
        if ag.state_db.exists():
            try:
                import sqlite3
                conn = sqlite3.connect(str(ag.state_db))
                info["session_count"] = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
                conn.close()
            except Exception:
                info["session_count"] = 0
        else:
            # Count jsonl files
            if ag.sessions_dir.exists():
                info["session_count"] = len(list(ag.sessions_dir.glob("*.jsonl")))
            else:
                info["session_count"] = 0

        if ag.skills_dir.exists():
            info["skill_count"] = len(list(ag.skills_dir.rglob("SKILL.md")))
        else:
            info["skill_count"] = 0

        if ag.cron_dir.exists():
            import json
            jobs_file = ag.cron_dir / "jobs.json"
            if jobs_file.exists():
                try:
                    info["cron_count"] = len(json.loads(jobs_file.read_text()).get("jobs", []))
                except Exception:
                    info["cron_count"] = 0
            else:
                info["cron_count"] = 0
        else:
            info["cron_count"] = 0

        result.append(info)
    return {"agents": result}
