"""System resources API."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

from hermes_dashboard.collectors.system import collect_system_status
from hermes_dashboard.schemas import SystemStatus

router = APIRouter()


@router.get("/status", response_model=SystemStatus)
async def get_system_status() -> SystemStatus:
    return collect_system_status()


@router.get("/stream")
async def stream_system() -> EventSourceResponse:
    async def generator():
        while True:
            yield {"data": collect_system_status().model_dump_json()}
            await asyncio.sleep(2)

    return EventSourceResponse(generator())
