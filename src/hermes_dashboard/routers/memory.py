"""Memory API."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from hermes_dashboard.collectors.memory import (
    get_memory_file,
    list_memory_files,
    update_memory_file,
)
from hermes_dashboard.schemas import MemoryFile

router = APIRouter()


@router.get("")
async def get_memory_files(agent: str = Query("")) -> dict:
    return list_memory_files(agent_id=agent)


@router.get("/{name}", response_model=MemoryFile)
async def get_memory(name: str, agent: str = Query("")) -> MemoryFile:
    f = get_memory_file(name, agent_id=agent)
    if not f:
        raise HTTPException(404, "Memory file not found")
    return f


@router.put("/{name}")
async def update_memory(name: str, body: dict, agent: str = Query("")):
    content = body.get("content", "")
    ok = update_memory_file(name, content, agent_id=agent)
    if not ok:
        raise HTTPException(400, "Could not update file (locked, read-only, or not found)")
    return {"status": "ok"}
