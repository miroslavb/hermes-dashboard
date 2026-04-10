"""Logs API."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException, Query
from sse_starlette.sse import EventSourceResponse

from hermes_dashboard.collectors.logs import list_log_files, tail_log
from hermes_dashboard.config import settings
from hermes_dashboard.schemas import LogFileInfo, LogTail

router = APIRouter()


@router.get("", response_model=list[LogFileInfo])
async def get_log_files() -> list[LogFileInfo]:
    return list_log_files()


@router.get("/{name}", response_model=LogTail)
async def get_log_tail(name: str, lines: int = Query(100, ge=1, le=5000)) -> LogTail:
    result = tail_log(name, lines=lines)
    if not result:
        raise HTTPException(404, "Log file not found")
    return result


@router.get("/{name}/stream")
async def stream_log(name: str) -> EventSourceResponse:
    if "/" in name or ".." in name:
        raise HTTPException(400, "Invalid filename")

    path = settings.logs_dir / name
    if not path.exists():
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
                    # File was rotated
                    offset = 0
            except OSError:
                pass
            await asyncio.sleep(1)

    return EventSourceResponse(generator())
