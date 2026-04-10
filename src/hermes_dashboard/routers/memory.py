"""Memory API."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from hermes_dashboard.collectors.memory import (
    get_memory_file,
    list_memory_files,
    update_memory_file,
)
from hermes_dashboard.schemas import MemoryFile

router = APIRouter()


@router.get("", response_model=list[MemoryFile])
async def get_memory_files() -> list[MemoryFile]:
    return list_memory_files()


@router.get("/{name}", response_model=MemoryFile)
async def get_memory(name: str) -> MemoryFile:
    f = get_memory_file(name)
    if not f:
        raise HTTPException(404, "Memory file not found")
    return f


@router.put("/{name}")
async def update_memory(name: str, body: dict):
    content = body.get("content", "")
    ok = update_memory_file(name, content)
    if not ok:
        raise HTTPException(400, "Could not update file (locked or not found)")
    return {"status": "ok"}
