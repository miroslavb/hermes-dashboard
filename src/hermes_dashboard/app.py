"""FastAPI application factory."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

STATIC_DIR = Path(__file__).parent / "static"


def create_app() -> FastAPI:
    app = FastAPI(
        title="Hermes Dashboard",
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
    )

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

    # Frontend
    @app.get("/")
    async def index():
        return FileResponse(STATIC_DIR / "index.html")

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    return app
