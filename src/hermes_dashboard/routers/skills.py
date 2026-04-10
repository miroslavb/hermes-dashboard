"""Skills API."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from hermes_dashboard.collectors.skills import (
    get_skill_content,
    list_categories,
    list_skills,
)
from hermes_dashboard.schemas import SkillCategory, SkillInfo

router = APIRouter()


@router.get("", response_model=list[SkillCategory])
async def get_categories() -> list[SkillCategory]:
    return list_categories()


@router.get("/{category}", response_model=list[SkillInfo])
async def get_category_skills(category: str) -> list[SkillInfo]:
    skills = list_skills(category)
    if not skills:
        raise HTTPException(404, "Category not found or empty")
    return skills


@router.get("/{category}/{name}")
async def get_skill(category: str, name: str):
    content = get_skill_content(category, name)
    if not content:
        raise HTTPException(404, "Skill not found")
    return {"name": name, "category": category, "content": content}
