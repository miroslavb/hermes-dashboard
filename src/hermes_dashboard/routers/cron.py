"""Cron jobs API."""

from __future__ import annotations

from fastapi import APIRouter, Query

from hermes_dashboard.collectors.cron_jobs import list_cron_jobs

router = APIRouter()


@router.get("")
async def get_cron_jobs(agent: str = Query("")) -> dict:
    return list_cron_jobs(agent_id=agent)
