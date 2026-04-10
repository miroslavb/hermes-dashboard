# 🖥 Hermes Dashboard

Real-time web dashboard for monitoring the [Hermes](https://github.com/nousresearch/hermes-agent) agent runtime.

![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)
![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)
![FastAPI](https://img.shields.io/badge/fastapi-0.115+-009688.svg)

## Features

- 📊 **System Resources** — CPU, RAM, disk, network in real-time (SSE)
- 🧠 **Memory** — View/edit MEMORY.md and USER.md
- 🛠 **Skills** — Browse 27 skill categories, view SKILL.md files
- 💬 **Sessions** — Browse and search session transcripts (FTS)
- ⚡ **Processes** — Active tool calls and subagents
- ⏰ **Cron** — Scheduled jobs and their status
- 📋 **Logs** — Live-tail gateway, agent, and error logs (SSE)

## Quick Start

```bash
pip install -e ".[dev]"
hermes-dashboard
# → http://localhost:8090
```

## Docker

```bash
docker compose up -d
# → http://localhost:8090
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `HERMES_HOME` | `~/.hermes` | Path to Hermes data directory |
| `DASHBOARD_HOST` | `0.0.0.0` | Bind address |
| `DASHBOARD_PORT` | `8090` | Listen port |
| `DASHBOARD_AUTH_TOKEN` | _(none)_ | Bearer token for auth |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/system/status` | System metrics snapshot |
| GET | `/api/system/stream` | SSE real-time metrics |
| GET | `/api/sessions` | List sessions (paginated) |
| GET | `/api/sessions/search?q=` | FTS search messages |
| GET | `/api/sessions/{id}` | Full session transcript |
| GET | `/api/skills` | List skill categories |
| GET | `/api/skills/{category}` | Skills in category |
| GET | `/api/skills/{cat}/{name}` | Full SKILL.md content |
| GET | `/api/memory` | List memory files |
| GET | `/api/memory/{file}` | Read memory file |
| PUT | `/api/memory/{file}` | Update memory file |
| GET | `/api/processes` | Active OS processes |
| GET | `/api/processes/active` | Recently active sessions |
| GET | `/api/cron` | List cron jobs |
| GET | `/api/cron/output` | Recent cron output |
| GET | `/api/logs` | List log files |
| GET | `/api/logs/{name}` | Tail log file |
| GET | `/api/logs/{name}/stream` | SSE live log tail |

## Development

```bash
make install   # install dependencies
make dev       # run in dev mode with reload
make test      # run tests
make lint      # ruff check + format
make format    # auto-fix lint + format
```

## Architecture

```
hermes-dashboard/
├── src/hermes_dashboard/
│   ├── app.py              # FastAPI factory
│   ├── config.py           # Settings from env
│   ├── schemas.py          # Pydantic models
│   ├── collectors/         # Data source readers
│   │   ├── system.py       # psutil metrics
│   │   ├── sessions.py     # state.db + JSON
│   │   ├── skills.py       # filesystem scan
│   │   ├── memory.py       # .md files
│   │   ├── processes.py    # OS processes
│   │   ├── cron_jobs.py    # cron dir
│   │   └── logs.py         # log tail
│   ├── routers/            # FastAPI endpoints
│   └── static/             # Frontend (vanilla JS)
└── tests/
```

## License

MIT
