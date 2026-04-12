"""Skills API."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from hermes_dashboard.collectors.skills import (
    get_skill_content,
    list_categories,
    list_skills,
)
from hermes_dashboard.schemas import SkillCategory, SkillInfo

router = APIRouter()


@router.get("")
async def get_categories(agent: str = Query("")) -> dict:
    return list_categories(agent_id=agent)


@router.get("/{category}", response_model=list[SkillInfo])
async def get_category_skills(category: str, agent: str = Query("")) -> list[SkillInfo]:
    skills = list_skills(category, agent_id=agent)
    if not skills:
        raise HTTPException(404, "Category not found or empty")
    return skills


@router.get("/{category}/{name}")
async def get_skill(category: str, name: str, agent: str = Query("")):
    result = get_skill_content(category, name, agent_id=agent)
    if not result["content"]:
        raise HTTPException(404, "Skill not found")
    return {"name": name, "category": category, **result}
