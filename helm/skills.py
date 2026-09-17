from pathlib import Path

import yaml

SKILL_DIRS = [
    Path.home() / ".agents" / "skills",
    Path.cwd() / ".agents" / "skills",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def _parse(path: Path) -> dict | None:
    """Pull the frontmatter out of a SKILL.md, or None if it is unusable."""
    text = _read(path)
    if not text.startswith("---"):
        return None

    parts = text.split("---", 2)
    if len(parts) < 3:
        return None

    meta = yaml.safe_load(parts[1])
    if not isinstance(meta, dict) or not meta.get("description"):
        return None

    return {
        "name": str(meta.get("name") or path.parent.name),
        "description": " ".join(str(meta["description"]).split()),
        "path": path,
    }


def load_skills(dirs: list | None = None) -> tuple[dict, list]:
    """Index every readable skill. Later directories win on name collisions."""
    skills = {}
    errors = []

    for directory in dirs if dirs is not None else SKILL_DIRS:
        for path in sorted(directory.glob("*/SKILL.md")):
            try:
                skill = _parse(path)
            except (OSError, UnicodeDecodeError, yaml.YAMLError) as e:
                errors.append(f"{path}: {type(e).__name__}")
                continue

            if skill is None:
                errors.append(f"{path}: needs frontmatter with a description")
            else:
                skills[skill["name"]] = skill

    return skills, errors


SKILLS, SKILL_ERRORS = load_skills()


def skills_prompt() -> str:
    return "\n".join(f"- {name}: {s['description']}" for name, s in SKILLS.items())


def read_skill(name: str) -> str:
    """Open a skill and return its full instructions."""
    skill = SKILLS.get(name)
    if skill is None:
        return f"Error: no skill named {name!r}. Available skills: {', '.join(SKILLS) or 'none'}."

    try:
        return _read(skill["path"])
    except OSError as e:
        return f"Error reading skill {name!r}: {e}"
