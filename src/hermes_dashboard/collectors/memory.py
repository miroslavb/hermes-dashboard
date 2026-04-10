"""Memory collector — reads ~/.hermes/memories/ .md files."""

from __future__ import annotations

from hermes_dashboard.config import settings
from hermes_dashboard.schemas import MemoryFile


def list_memory_files() -> list[MemoryFile]:
    """List memory files (MEMORY.md, USER.md)."""
    mem_dir = settings.memories_dir
    if not mem_dir.exists():
        return []

    files = []
    for f in sorted(mem_dir.iterdir()):
        if f.is_file() and f.suffix == ".md" and not f.name.endswith(".lock"):
            stat = f.stat()
            files.append(
                MemoryFile(
                    name=f.name,
                    size=stat.st_size,
                    modified=stat.st_mtime,
                    content=f.read_text() if stat.st_size < 100_000 else "",
                )
            )

    return files


def get_memory_file(name: str) -> MemoryFile | None:
    """Read a specific memory file."""
    # Sanitize name
    if "/" in name or ".." in name or not name.endswith(".md"):
        return None

    path = settings.memories_dir / name
    if not path.exists():
        return None

    stat = path.stat()
    return MemoryFile(
        name=name,
        size=stat.st_size,
        modified=stat.st_mtime,
        content=path.read_text(),
    )


def update_memory_file(name: str, content: str) -> bool:
    """Write content to a memory file."""
    if "/" in name or ".." in name or not name.endswith(".md"):
        return False

    path = settings.memories_dir / name
    if not path.exists():
        return False

    # Check lock
    lock_path = path.with_suffix(".md.lock")
    if lock_path.exists() and lock_path.stat().st_size > 0:
        return False

    path.write_text(content)
    return True
