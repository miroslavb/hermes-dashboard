"""Cron jobs collector — scans cron directories across agents."""

from __future__ import annotations

import json
import time

from hermes_dashboard.config import settings


def list_cron_jobs(agent_id: str = "") -> dict:
    """List scheduled cron jobs grouped by agent."""
    agents = settings.get_agents_for_query(agent_id)
    result = {}

    for ag in agents:
        agent_data = {"jobs": [], "outputs": []}
        cron_dir = ag.cron_dir

        if cron_dir.exists():
            # Jobs
            for f in sorted(cron_dir.glob("*.json")):
                if f.name.startswith("."):
                    continue
                try:
                    data = json.loads(f.read_text())
                    agent_data["jobs"].append({
                        "id": data.get("id", f.stem),
                        "name": data.get("name", f.stem),
                        "schedule": data.get("schedule", ""),
                        "prompt": data.get("prompt", "")[:200],
                        "status": data.get("status", "active"),
                        "last_run": data.get("last_run"),
                    })
                except (json.JSONDecodeError, OSError):
                    continue

            # Outputs
            output_dir = cron_dir / "output"
            if output_dir.exists():
                for f in sorted(output_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True)[:20]:
                    if f.is_file():
                        stat = f.stat()
                        agent_data["outputs"].append({
                            "file": f.name,
                            "size": stat.st_size,
                            "modified": stat.st_mtime,
                            "age_seconds": round(time.time() - stat.st_mtime, 1),
                            "preview": f.read_text()[:500] if stat.st_size < 100_000 else "",
                        })

        result[ag.id] = {
            "name": ag.name,
            **agent_data,
        }

    return result
