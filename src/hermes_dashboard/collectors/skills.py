"""Skills collector — scans ~/.hermes/skills/ directory tree."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from hermes_dashboard.config import settings
from hermes_dashboard.schemas import SkillCategory, SkillInfo


def list_categories() -> list[SkillCategory]:
    """List skill categories with skill counts."""
    skills_dir = settings.skills_dir
    if not skills_dir.exists():
        return []

    categories = []
    for d in sorted(skills_dir.iterdir()):
        if not d.is_dir() or d.name.startswith("."):
            continue
        desc_file = d / "DESCRIPTION.md"
        desc = ""
        if desc_file.exists():
            desc = desc_file.read_text().strip()[:200]

        # Count skills (SKILL.md files recursively)
        skill_count = len(list(d.rglob("SKILL.md")))

        categories.append(SkillCategory(name=d.name, description=desc, skill_count=skill_count))

    return categories


def list_skills(category: str) -> list[SkillInfo]:
    """List skills in a specific category."""
    cat_dir = settings.skills_dir / category
    if not cat_dir.exists():
        return []

    skills = []
    for skill_md in sorted(cat_dir.rglob("SKILL.md")):
        info = _parse_skill_md(skill_md, category)
        skills.append(info)

    return skills


def get_skill_content(category: str, name: str) -> str:
    """Get full SKILL.md content for a skill."""
    cat_dir = settings.skills_dir / category
    if not cat_dir.exists():
        return ""

    # Try direct path: category/name/SKILL.md
    direct = cat_dir / name / "SKILL.md"
    if direct.exists():
        return direct.read_text()

    # Try flat: category/SKILL.md (when name == category)
    flat = cat_dir / "SKILL.md"
    if flat.exists() and name == category:
        return flat.read_text()

    # Search recursively
    for skill_md in cat_dir.rglob("SKILL.md"):
        if skill_md.parent.name == name:
            return skill_md.read_text()

    return ""


def _parse_skill_md(path: Path, category: str) -> SkillInfo:
    """Parse YAML frontmatter from SKILL.md."""
    content = path.read_text()
    name = path.parent.name
    desc = ""
    tags: list[str] = []

    # Extract YAML frontmatter
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

    # Fallback: first heading
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
