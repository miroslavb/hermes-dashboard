"""Sessions API."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from hermes_dashboard.collectors.sessions import (
    get_session,
    list_sessions,
    search_sessions,
)
from hermes_dashboard.schemas import SessionDetail, SessionSummary

router = APIRouter()


@router.get("", response_model=list[SessionSummary])
async def get_sessions(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    agent: str = Query(""),
) -> list[SessionSummary]:
    return list_sessions(limit=limit, offset=offset, agent_id=agent)


@router.get("/search")
async def search(q: str = Query(..., min_length=2), limit: int = Query(20, ge=1, le=100)):
    return search_sessions(q, limit=limit)


@router.get("/{session_id}", response_model=SessionDetail)
async def get_session_detail(session_id: str, agent: str = Query("")) -> SessionDetail:
    session = get_session(session_id, agent_id=agent)
    if not session:
        raise HTTPException(404, "Session not found")
    return session
