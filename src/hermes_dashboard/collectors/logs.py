"""Logs collector — tail and stream log files."""

from __future__ import annotations

from pathlib import Path

from hermes_dashboard.config import settings
from hermes_dashboard.schemas import LogFileInfo, LogTail


def list_log_files() -> list[LogFileInfo]:
    """List available log files."""
    logs_dir = settings.logs_dir
    if not logs_dir.exists():
        return []

    files = []
    for f in sorted(logs_dir.glob("*.log")):
        stat = f.stat()
        files.append(LogFileInfo(name=f.name, size=stat.st_size, modified=stat.st_mtime))

    return files


def tail_log(name: str, lines: int = 100) -> LogTail | None:
    """Read last N lines from a log file."""
    if "/" in name or ".." in name:
        return None

    path = settings.logs_dir / name
    if not path.exists():
        return None

    content = path.read_text(errors="replace")
    all_lines = content.splitlines()
    tail = all_lines[-lines:] if len(all_lines) > lines else all_lines

    return LogTail(
        file=name,
        lines=tail,
        total_lines=len(all_lines),
    )


def read_log_bytes(name: str, offset: int = 0, size: int = 8192) -> bytes | None:
    """Read raw bytes from a log file (for SSE streaming)."""
    if "/" in name or ".." in name:
        return None

    path = settings.logs_dir / name
    if not path.exists():
        return None

    with open(path, "rb") as f:
        if offset:
            f.seek(offset)
        return f.read(size)
