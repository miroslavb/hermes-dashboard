# 🖥 Hermes Dashboard

Real-time web dashboard for monitoring [Hermes](https://github.com/nousresearch/hermes-agent) agent runtimes. Supports multiple agents with per-agent filtering across all panels.

![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)
![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)
![FastAPI](https://img.shields.io/badge/fastapi-0.115+-009688.svg)

## Features

- 📊 **System Resources** — CPU, RAM, disk, network in real-time (SSE) with Chart.js graphs
- 🧠 **Memory** — View/edit MEMORY.md, USER.md, SOUL.md per agent (SOUL.md read-only)
- 🛠 **Skills** — Browse skill categories per agent, view full SKILL.md content
- 💬 **Sessions** — Browse session transcripts per agent
- ⚡ **Processes** — Active OS processes and gateway status
- ⏰ **Cron** — Scheduled jobs per agent with output viewer
- 📋 **Logs** — Live-tail logs per agent (SSE)
- 💾 **Backup** — Snapshot list, manual run trigger, restore command generator
- 🔄 **Multi-Agent** — Agent selector dropdown filters all panels by specific agent or shows all

## Quick Start

```bash
pip install -e ".[dev]"
DASHBOARD_TOKEN=your-secret hermes-dashboard
# → http://localhost:8090?token=your-secret
```

## Docker

```bash
docker compose up -d
# → http://localhost:8090
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `HERMES_HOME` | `~/.hermes` | Path to primary agent data directory |
| `HERMES_HOME2` | `~/.hermes-agent2` | Path to secondary agent data directory |
| `DASHBOARD_HOST` | `0.0.0.0` | Bind address |
| `DASHBOARD_PORT` | `8090` | Listen port |
| `DASHBOARD_TOKEN` | _(auto-generated)_ | Bearer token for auth |

## API Endpoints

### System
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/system/status` | System metrics snapshot |
| GET | `/api/system/stream` | SSE real-time metrics |

### Agents
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/agents` | List all agents with session/skill/cron counts |

### Sessions
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/sessions?agent=` | List sessions (optional `?agent=` filter) |
| GET | `/api/sessions/{agent}/{id}` | Full session transcript |

### Skills
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/skills?agent=` | List skill categories |
| GET | `/api/skills/{agent}/{category}` | Skills in category |
| GET | `/api/skills/{agent}/{cat}/{name}` | Full SKILL.md content |

### Memory
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/memory?agent=` | List memory files grouped by agent |
| GET | `/api/memory/{agent}/{name}` | Read specific memory file |
| PUT | `/api/memory/{agent}/{name}` | Update memory file (SOUL.md is read-only) |

### Processes
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/processes` | Active OS processes and gateway status |
| GET | `/api/processes/stream` | SSE real-time process updates |

### Cron
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/cron?agent=` | List cron jobs per agent |
| GET | `/api/cron/output?agent=` | Recent cron job output |

### Logs
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/logs?agent=` | List log files per agent |
| GET | `/api/logs/{name}?agent=&lines=` | Tail log file |
| GET | `/api/logs/{name}/stream?agent=` | SSE live log tail |

### Backup
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/backup/status` | Backup status, snapshots, log |
| POST | `/api/backup/run` | Trigger manual backup |
| POST | `/api/backup/restore` | Get restore command for snapshot |

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
│   ├── app.py              # FastAPI factory + auth middleware + no-cache headers
│   ├── config.py           # AgentConfig dataclass, multi-agent settings
│   ├── schemas.py          # Pydantic models
│   ├── collectors/         # Data source readers (all support agent_id param)
│   │   ├── system.py       # psutil metrics
│   │   ├── sessions.py     # state.db + JSON transcripts
│   │   ├── skills.py       # filesystem scan
│   │   ├── memory.py       # .md files (SOUL.md, MEMORY.md, USER.md)
│   │   ├── processes.py    # OS processes + gateway status
│   │   ├── cron_jobs.py    # cron dir scan
│   │   ├── logs.py         # log tail
│   │   └── backup.py       # snapshot list + rsync trigger
│   ├── routers/            # FastAPI endpoints
│   │   ├── agents.py       # GET /api/agents
│   │   ├── system.py
│   │   ├── sessions.py
│   │   ├── skills.py
│   │   ├── memory.py
│   │   ├── processes.py
│   │   ├── cron.py
│   │   ├── logs.py
│   │   └── backup.py
│   └── static/             # Frontend (vanilla JS, no frameworks)
│       ├── index.html
│       ├── favicon.svg
│       ├── css/app.css
│       └── js/
│           ├── app.js      # Shell: routing, agent selector, fetchApi, SSE helper
│           ├── system.js   # CPU/RAM/disk gauges + Chart.js history
│           ├── sessions.js # Session list + transcript modal
│           ├── skills.js   # Category tree + skill detail viewer
│           ├── memory.js   # File list + inline editor
│           ├── processes.js
│           ├── cron.js     # Job list + output viewer
│           ├── logs.js     # File list + live-tail viewer
│           └── backup.js   # Snapshots + run + restore
└── tests/
```

## License

MIT
