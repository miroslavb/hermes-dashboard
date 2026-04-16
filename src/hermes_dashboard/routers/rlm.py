"""RLM trajectory API."""

from __future__ import annotations

from fastapi import HTTPException, Query

from hermes_dashboard.collectors.rlm import get_rlm_run, list_rlm_runs
from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def get_rlm_runs(agent: str = Query("")) -> list[dict]:
    """List all RLM trajectory runs."""
    return list_rlm_runs(agent_id=agent)


@router.get("/{filename}")
async def get_rlm_run_detail(filename: str, agent: str = Query("")):
    """Get full trajectory data for a specific RLM run."""
    if "/" in filename or ".." in filename or not filename.endswith(".jsonl"):
        raise HTTPException(400, "Invalid filename")

    result = get_rlm_run(filename, agent_id=agent)
    if not result:
        raise HTTPException(404, "RLM run not found")
    return result
