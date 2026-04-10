"""Dashboard configuration — reads from env vars with sensible defaults."""

import os
from pathlib import Path


class Settings:
    def __init__(self) -> None:
        self.hermes_home = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
        self.host = os.environ.get("DASHBOARD_HOST", "0.0.0.0")
        self.port = int(os.environ.get("DASHBOARD_PORT", "8090"))
        self.auth_token = os.environ.get("DASHBOARD_AUTH_TOKEN", "")

        # Derived paths
        self.sessions_dir = self.hermes_home / "sessions"
        self.skills_dir = self.hermes_home / "skills"
        self.memories_dir = self.hermes_home / "memories"
        self.logs_dir = self.hermes_home / "logs"
        self.cron_dir = self.hermes_home / "cron"
        self.state_db = self.hermes_home / "state.db"


settings = Settings()
