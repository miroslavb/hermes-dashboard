"""Processes API."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

from hermes_dashboard.collectors.processes import (
    list_active_sessions,
    list_hermes_processes,
)
from hermes_dashboard.schemas import ProcessInfo

router = APIRouter()


@router.get("", response_model=list[ProcessInfo])
async def get_processes() -> list[ProcessInfo]:
    return list_hermes_processes()


@router.get("/stream")
async def stream_processes() -> EventSourceResponse:
    import json

    async def generator():
        while True:
            processes = list_hermes_processes()
            yield {"data": json.dumps([p.model_dump(mode="json") for p in processes])}
            await asyncio.sleep(5)

    return EventSourceResponse(generator())


@router.get("/active")
async def get_active_sessions():
    return list_active_sessions()
