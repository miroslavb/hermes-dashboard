"""Usage API — token stats, costs, and breakdowns."""

from __future__ import annotations

from fastapi import APIRouter, Query

from hermes_dashboard.collectors.usage import get_usage_summary

router = APIRouter()


@router.get("")
async def usage(
    agent: str = Query("", description="Filter by agent ID"),
    date_from: str = Query("", description="Start date (ISO format, e.g. 2026-04-01)"),
    date_to: str = Query("", description="End date (ISO format, e.g. 2026-04-16)"),
    provider: str = Query("", description="Filter by billing provider (e.g. nous, openrouter)"),
    model: str = Query("", description="Filter by model name"),
) -> dict:
    """Get token usage summary with optional filters."""
    return get_usage_summary(
        agent_id=agent,
        date_from=date_from,
        date_to=date_to,
        provider=provider,
        model=model,
    )
