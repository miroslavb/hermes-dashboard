"""Processes API."""

from __future__ import annotations

from fastapi import APIRouter

from hermes_dashboard.collectors.processes import (
    list_active_sessions,
    list_hermes_processes,
)
from hermes_dashboard.schemas import ProcessInfo

router = APIRouter()


@router.get("", response_model=list[ProcessInfo])
async def get_processes() -> list[ProcessInfo]:
    return list_hermes_processes()


@router.get("/active")
async def get_active_sessions():
    return list_active_sessions()
