"""Processes collector — active Hermes-related OS processes."""

from __future__ import annotations

import time

import psutil

from hermes_dashboard.config import settings
from hermes_dashboard.schemas import ProcessInfo


def list_hermes_processes() -> list[ProcessInfo]:
    """Find processes related to Hermes agent."""
    results = []

    for proc in psutil.process_iter(
        ["pid", "name", "cpu_percent", "memory_info", "cmdline", "create_time"]
    ):
        try:
            info = proc.info
            cmdline = " ".join(info.get("cmdline") or [])
            name = info.get("name", "")

            # Filter: Python/node processes mentioning hermes
            if not any(kw in cmdline.lower() for kw in ["hermes", "beelzebub"]):
                continue

            mem_info = info.get("memory_info")
            results.append(
                ProcessInfo(
                    pid=info["pid"],
                    name=name,
                    cpu_percent=info.get("cpu_percent", 0) or 0,
                    memory_mb=round(mem_info.rss / 1e6, 1) if mem_info else 0,
                    cmdline=cmdline[:200],
                    create_time=info.get("create_time", 0),
                )
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return results


def list_active_sessions() -> list[dict]:
    """List sessions modified in the last 5 minutes."""
    sessions_dir = settings.sessions_dir
    if not sessions_dir.exists():
        return []

    cutoff = time.time() - 300  # 5 minutes
    active = []

    for f in sessions_dir.glob("*.json"):
        if f.name.startswith("sessions.json"):
            continue
        stat = f.stat()
        if stat.st_mtime > cutoff:
            active.append(
                {
                    "file": f.name,
                    "size": stat.st_size,
                    "modified": stat.st_mtime,
                    "age_seconds": round(time.time() - stat.st_mtime, 1),
                }
            )

    return sorted(active, key=lambda x: x["modified"], reverse=True)
