"""FastAPI application factory."""

from __future__ import annotations

import os
import secrets
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

STATIC_DIR = Path(__file__).parent / "static"

# Auth token — generated once per process or read from env
DASHBOARD_TOKEN = os.environ.get("DASHBOARD_TOKEN", secrets.token_urlsafe(24))


def create_app() -> FastAPI:
    app = FastAPI(
        title="Hermes Dashboard",
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
    )

    # Token auth middleware
    @app.middleware("http")
    async def token_auth(request: Request, call_next):
        path = request.url.path
        # Skip auth for health check and static assets
        if path == "/health" or path.startswith("/static/"):
            return await call_next(request)
        # Check token from query param or header
        token = request.query_params.get("token") or request.headers.get(
            "Authorization", ""
        ).removeprefix("Bearer ")
        if not token or not secrets.compare_digest(token, DASHBOARD_TOKEN):
            body = (
                '<html><body style="'
                "background:#1a1a2e;color:#e0e0e0;"
                'font-family:sans-serif;text-align:center;padding:3rem">'
                "<h1>\U0001f512 Hermes Dashboard</h1>"
                "<p>Access denied. Add "
                "<code>?token=YOUR_TOKEN</code> to the URL.</p>"
                "</body></html>"
            )
            return HTMLResponse(body, status_code=401)
        return await call_next(request)

    # API routers
    from hermes_dashboard.routers.cron import router as cron_router
    from hermes_dashboard.routers.logs import router as logs_router
    from hermes_dashboard.routers.memory import router as memory_router
    from hermes_dashboard.routers.processes import router as processes_router
    from hermes_dashboard.routers.sessions import router as sessions_router
    from hermes_dashboard.routers.skills import router as skills_router
    from hermes_dashboard.routers.system import router as system_router

    app.include_router(system_router, prefix="/api/system", tags=["system"])
    app.include_router(sessions_router, prefix="/api/sessions", tags=["sessions"])
    app.include_router(skills_router, prefix="/api/skills", tags=["skills"])
    app.include_router(memory_router, prefix="/api/memory", tags=["memory"])
    app.include_router(processes_router, prefix="/api/processes", tags=["processes"])
    app.include_router(cron_router, prefix="/api/cron", tags=["cron"])
    app.include_router(logs_router, prefix="/api/logs", tags=["logs"])

    # Health check (no auth required)
    @app.get("/health")
    async def health():
        return {"status": "ok"}

    # Frontend
    @app.get("/")
    async def index():
        return FileResponse(STATIC_DIR / "index.html")

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    return app
