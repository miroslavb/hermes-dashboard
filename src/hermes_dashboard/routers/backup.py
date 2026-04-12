"""Backup API — status, run, restore."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from hermes_dashboard.collectors import backup as backup_collector

router = APIRouter()


@router.get("/status")
async def backup_status():
    """Current backup status, snapshots, and log tail."""
    return backup_collector.get_status()


@router.post("/run")
async def backup_run():
    """Launch a full backup now."""
    return backup_collector.run_backup()


class RestoreRequest(BaseModel):
    snapshot: str
    target: str = "/"


@router.post("/restore")
async def backup_restore(body: RestoreRequest):
    """Get restore command for a snapshot (does not execute)."""
    return backup_collector.get_restore_command(body.snapshot, body.target)
