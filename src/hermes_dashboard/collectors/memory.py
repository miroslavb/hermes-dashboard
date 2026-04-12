"""Memory collector — reads ~/.hermes/memories/ and ~/.hermes-agent2/memories/ .md files."""

from __future__ import annotations

from hermes_dashboard.config import AgentConfig, settings
from hermes_dashboard.schemas import MemoryFile


def list_memory_files(agent_id: str = "") -> dict:
    """List memory files grouped by agent."""
    agents = settings.get_agents_for_query(agent_id)
    result = {}

    for ag in agents:
        agent_files = []
        mem_dir = ag.memories_dir
        if mem_dir.exists():
            for f in sorted(mem_dir.iterdir()):
                if f.is_file() and f.suffix == ".md" and not f.name.endswith(".lock"):
                    stat = f.stat()
                    agent_files.append(
                        MemoryFile(
                            name=f.name,
                            size=stat.st_size,
                            modified=stat.st_mtime,
                            content=f.read_text() if stat.st_size < 100_000 else "",
                        )
                    )

        # Also include SOUL.md from agent root
        if ag.soul_file.exists():
            stat = ag.soul_file.stat()
            agent_files.insert(0,
                MemoryFile(
                    name="SOUL.md",
                    size=stat.st_size,
                    modified=stat.st_mtime,
                    content=ag.soul_file.read_text() if stat.st_size < 100_000 else "",
                )
            )

        result[ag.id] = {
            "name": ag.name,
            "files": agent_files,
        }

    return result


def get_memory_file(name: str, agent_id: str = "") -> MemoryFile | None:
    """Read a specific memory file from a specific agent."""
    if "/" in name or ".." in name:
        return None

    agents = settings.get_agents_for_query(agent_id)
    for ag in agents:
        # Check SOUL.md in root
        if name == "SOUL.md" and ag.soul_file.exists():
            stat = ag.soul_file.stat()
            return MemoryFile(
                name=name,
                size=stat.st_size,
                modified=stat.st_mtime,
                content=ag.soul_file.read_text(),
            )

        # Check memories dir
        if not name.endswith(".md"):
            continue
        path = ag.memories_dir / name
        if path.exists():
            stat = path.stat()
            return MemoryFile(
                name=name,
                size=stat.st_size,
                modified=stat.st_mtime,
                content=path.read_text(),
            )

    return None


def update_memory_file(name: str, content: str, agent_id: str = "") -> bool:
    """Write content to a memory file."""
    if "/" in name or ".." in name or not name.endswith(".md"):
        return False
    if name == "SOUL.md":
        return False  # SOUL.md is read-only

    agents = settings.get_agents_for_query(agent_id)
    for ag in agents:
        path = ag.memories_dir / name
        if path.exists():
            lock_path = path.with_suffix(".md.lock")
            if lock_path.exists() and lock_path.stat().st_size > 0:
                return False
            path.write_text(content)
            return True

    return False
