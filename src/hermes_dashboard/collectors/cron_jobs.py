"""Cron jobs collector — scans ~/.hermes/cron/ directory."""

from __future__ import annotations

import json
import time

from hermes_dashboard.config import settings
from hermes_dashboard.schemas import CronJob


def list_cron_jobs() -> list[CronJob]:
    """List scheduled cron jobs."""
    cron_dir = settings.cron_dir
    if not cron_dir.exists():
        return []

    jobs = []
    # Look for job definition files (JSON)
    for f in sorted(cron_dir.glob("*.json")):
        if f.name.startswith("."):
            continue
        try:
            data = json.loads(f.read_text())
            jobs.append(
                CronJob(
                    id=data.get("id", f.stem),
                    name=data.get("name", f.stem),
                    schedule=data.get("schedule", ""),
                    prompt=data.get("prompt", "")[:200],
                    status=data.get("status", "active"),
                    last_run=data.get("last_run"),
                )
            )
        except (json.JSONDecodeError, OSError):
            continue

    return jobs


def list_cron_output(limit: int = 20) -> list[dict]:
    """List recent cron output files."""
    output_dir = settings.cron_dir / "output"
    if not output_dir.exists():
        return []

    results = []
    for f in sorted(
        output_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True
    )[:limit]:
        if f.is_file():
            stat = f.stat()
            results.append(
                {
                    "file": f.name,
                    "size": stat.st_size,
                    "modified": stat.st_mtime,
                    "age_seconds": round(time.time() - stat.st_mtime, 1),
                    "preview": f.read_text()[:500] if stat.st_size < 100_000 else "",
                }
            )

    return results
