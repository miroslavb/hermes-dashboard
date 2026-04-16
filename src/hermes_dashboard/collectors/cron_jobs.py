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
                    # Handle jobs.json with {jobs: [...]} structure
                    if f.name == "jobs.json" and isinstance(data, dict) and "jobs" in data:
                        for job in data["jobs"]:
                            schedule = job.get("schedule", "")
                            # Schedule can be a dict with display field or a string
                            if isinstance(schedule, dict):
                                schedule = schedule.get("display", str(schedule))
                            agent_data["jobs"].append({
                                "id": job.get("id", ""),
                                "name": job.get("name", ""),
                                "schedule": schedule,
                                "prompt": (job.get("prompt", "") or "")[:200],
                                "status": "active" if job.get("enabled", True) and not job.get("paused_at") else "paused",
                                "last_run": job.get("last_run_at"),
                            })
                    # Handle individual job files
                    elif isinstance(data, dict):
                        agent_data["jobs"].append({
                            "id": data.get("id", f.stem),
                            "name": data.get("name", f.stem),
                            "schedule": data.get("schedule", ""),
                            "prompt": (data.get("prompt", "") or "")[:200],
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
