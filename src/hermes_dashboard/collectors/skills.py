"""Skills collector — scans skills directories across all agents."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from hermes_dashboard.config import settings
from hermes_dashboard.schemas import SkillCategory, SkillInfo


def list_categories(agent_id: str = "") -> dict:
    """List skill categories grouped by agent."""
    agents = settings.get_agents_for_query(agent_id)
    result = {}

    for ag in agents:
        skills_dir = ag.skills_dir
        categories = []
        if skills_dir.exists():
            for d in sorted(skills_dir.iterdir()):
                if not d.is_dir() or d.name.startswith("."):
                    continue
                desc_file = d / "DESCRIPTION.md"
                desc = ""
                if desc_file.exists():
                    desc = desc_file.read_text().strip()[:200]
                skill_count = len(list(d.rglob("SKILL.md")))
                if skill_count > 0:
                    categories.append(SkillCategory(name=d.name, description=desc, skill_count=skill_count))

        result[ag.id] = {
            "name": ag.name,
            "categories": categories,
            "total": sum(c.skill_count for c in categories),
        }

    return result


def list_skills(category: str, agent_id: str = "") -> list[SkillInfo]:
    """List skills in a specific category."""
    agents = settings.get_agents_for_query(agent_id)
    skills = []
    for ag in agents:
        cat_dir = ag.skills_dir / category
        if not cat_dir.exists():
            continue
        for skill_md in sorted(cat_dir.rglob("SKILL.md")):
            info = _parse_skill_md(skill_md, category)
            skills.append(info)
    return skills


def get_skill_content(category: str, name: str, agent_id: str = "") -> dict:
    """Get full SKILL.md content for a skill. Returns content + agent info."""
    agents = settings.get_agents_for_query(agent_id)
    for ag in agents:
        cat_dir = ag.skills_dir / category
        if not cat_dir.exists():
            continue

        # Try direct path: category/name/SKILL.md
        direct = cat_dir / name / "SKILL.md"
        if direct.exists():
            return {"content": direct.read_text(), "agent": ag.id}

        # Search recursively
        for skill_md in cat_dir.rglob("SKILL.md"):
            if skill_md.parent.name == name:
                return {"content": skill_md.read_text(), "agent": ag.id}

    return {"content": "", "agent": ""}


def _parse_skill_md(path: Path, category: str) -> SkillInfo:
    """Parse YAML frontmatter from SKILL.md."""
    content = path.read_text()
    name = path.parent.name
    desc = ""
    tags: list[str] = []

    match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if match:
        try:
            fm = yaml.safe_load(match.group(1))
            if isinstance(fm, dict):
                name = fm.get("name", name)
                desc = fm.get("description", "")[:200]
                tags = fm.get("tags", []) if isinstance(fm.get("tags"), list) else []
        except yaml.YAMLError:
            pass

    if not desc:
        heading_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if heading_match:
            desc = heading_match.group(1)[:200]

    return SkillInfo(
        name=name,
        category=category,
        description=desc,
        tags=tags,
    )
