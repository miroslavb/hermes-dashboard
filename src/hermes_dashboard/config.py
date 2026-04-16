"""Dashboard configuration — reads from env vars with sensible defaults."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class AgentConfig:
    """Configuration for a single agent."""
    id: str
    name: str
    home: Path

    @property
    def sessions_dir(self) -> Path:
        return self.home / "sessions"

    @property
    def skills_dir(self) -> Path:
        return self.home / "skills"

    @property
    def memories_dir(self) -> Path:
        return self.home / "memories"

    @property
    def logs_dir(self) -> Path:
        return self.home / "logs"

    @property
    def cron_dir(self) -> Path:
        return self.home / "cron"

    @property
    def rlm_logs_dir(self) -> Path:
        return self.home / "rlm_logs"

    @property
    def state_db(self) -> Path:
        return self.home / "state.db"

    @property
    def soul_file(self) -> Path:
        return self.home / "SOUL.md"

    def exists(self) -> bool:
        return self.home.exists()


class Settings:
    def __init__(self) -> None:
        self.hermes_home = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
        self.host = os.environ.get("DASHBOARD_HOST", "0.0.0.0")
        self.port = int(os.environ.get("DASHBOARD_PORT", "8090"))
        self.auth_token = os.environ.get("DASHBOARD_AUTH_TOKEN", "")

        # Agent registry — discovered from filesystem
        self._agents: list[AgentConfig] | None = None

    @property
    def agents(self) -> list[AgentConfig]:
        """Discover and return all available agents."""
        if self._agents is not None:
            return self._agents

        candidates = [
            AgentConfig(id="hermes", name="Hermes", home=Path.home() / ".hermes"),
            AgentConfig(id="hermes2", name="Hermes 2 (Tatiyana)", home=Path.home() / ".hermes-agent2"),
            AgentConfig(id="hermes-rlm-repl", name="Hermes-REPL (RLM)", home=Path.home() / ".hermes-rlm-repl"),
            AgentConfig(id="hermes3", name="Hermes3", home=Path.home() / ".hermes-hermes3"),
        ]
        self._agents = [a for a in candidates if a.exists()]
        return self._agents

    def get_agent(self, agent_id: str) -> AgentConfig | None:
        """Get agent by ID."""
        for a in self.agents:
            if a.id == agent_id:
                return a
        return None

    def get_agents_for_query(self, agent_id: str = "") -> list[AgentConfig]:
        """Return agents filtered by query param, or all if empty."""
        if agent_id:
            a = self.get_agent(agent_id)
            return [a] if a else []
        return self.agents

    # Legacy compatibility — primary agent paths
    @property
    def sessions_dir(self) -> Path:
        return self.hermes_home / "sessions"

    @property
    def skills_dir(self) -> Path:
        return self.hermes_home / "skills"

    @property
    def memories_dir(self) -> Path:
        return self.hermes_home / "memories"

    @property
    def logs_dir(self) -> Path:
        return self.hermes_home / "logs"

    @property
    def cron_dir(self) -> Path:
        return self.hermes_home / "cron"

    @property
    def state_db(self) -> Path:
        return self.hermes_home / "state.db"


settings = Settings()
