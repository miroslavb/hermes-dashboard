"""Logs API."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException, Query
from sse_starlette.sse import EventSourceResponse

from hermes_dashboard.collectors.logs import list_log_files, tail_log
from hermes_dashboard.config import settings

router = APIRouter()


@router.get("")
async def get_log_files(agent: str = Query("")) -> dict:
    return list_log_files(agent_id=agent)


@router.get("/{name}")
async def get_log_tail(name: str, agent: str = Query(""), lines: int = Query(100, ge=1, le=5000)):
    result = tail_log(name, agent_id=agent, lines=lines)
    if not result:
        raise HTTPException(404, "Log file not found")
    return result


@router.get("/{name}/stream")
async def stream_log(name: str, agent: str = Query("")) -> EventSourceResponse:
    if "/" in name or ".." in name:
        raise HTTPException(400, "Invalid filename")

    # Find log file in agent's logs dir
    agents = settings.get_agents_for_query(agent)
    path = None
    for ag in agents:
        p = ag.logs_dir / name
        if p.exists():
            path = p
            break

    if not path:
        raise HTTPException(404, "Log file not found")

    async def generator():
        offset = path.stat().st_size
        while True:
            try:
                current_size = path.stat().st_size
                if current_size > offset:
                    with open(path, "rb") as f:
                        f.seek(offset)
                        data = f.read(current_size - offset)
                        offset = current_size
                        for line in data.decode(errors="replace").splitlines():
                            yield {"data": line}
                elif current_size < offset:
                    offset = 0
            except OSError:
                pass
            await asyncio.sleep(1)

    return EventSourceResponse(generator())
