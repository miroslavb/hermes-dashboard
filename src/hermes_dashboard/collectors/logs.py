"""Logs collector — tail and stream log files across agents."""

from __future__ import annotations

from hermes_dashboard.config import settings


def list_log_files(agent_id: str = "") -> dict:
    """List available log files grouped by agent."""
    agents = settings.get_agents_for_query(agent_id)
    result = {}
    for ag in agents:
        files = []
        if ag.logs_dir.exists():
            for f in sorted(ag.logs_dir.glob("*.log")):
                stat = f.stat()
                files.append({"name": f.name, "size": stat.st_size, "modified": stat.st_mtime})
        result[ag.id] = {"name": ag.name, "files": files}
    return result


def tail_log(name: str, agent_id: str = "", lines: int = 100) -> dict | None:
    """Read last N lines from a log file."""
    if "/" in name or ".." in name:
        return None

    agents = settings.get_agents_for_query(agent_id)
    for ag in agents:
        path = ag.logs_dir / name
        if path.exists():
            content = path.read_text(errors="replace")
            all_lines = content.splitlines()
            tail = all_lines[-lines:] if len(all_lines) > lines else all_lines
            return {
                "file": name,
                "lines": tail,
                "total_lines": len(all_lines),
                "agent": ag.id,
            }
    return None
