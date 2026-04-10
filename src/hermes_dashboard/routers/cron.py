"""Cron jobs API."""

from __future__ import annotations

from fastapi import APIRouter

from hermes_dashboard.collectors.cron_jobs import list_cron_jobs, list_cron_output
from hermes_dashboard.schemas import CronJob

router = APIRouter()


@router.get("", response_model=list[CronJob])
async def get_cron_jobs() -> list[CronJob]:
    return list_cron_jobs()


@router.get("/output")
async def get_cron_output(limit: int = 20):
    return list_cron_output(limit=limit)
