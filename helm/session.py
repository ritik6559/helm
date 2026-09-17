import json
from datetime import datetime
from pathlib import Path

from . import todos

DIR = Path.home() / ".helm" / "sessions"


def new_name() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def _file(name: str) -> Path:
    return DIR / f"{name}.json"


def save(name: str, messages: list) -> None:
    DIR.mkdir(parents=True, exist_ok=True)
    data = {"cwd": str(Path.cwd()), "messages": messages, "todos": todos.TODOS}

    temp = _file(name).with_suffix(".tmp")
    temp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    temp.replace(_file(name))


def _read(file: Path) -> dict | None:
    try:
        return json.loads(file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def load(name: str) -> list | None:
    """Return a session's messages, restoring its todo list as a side effect."""
    data = _read(_file(name))
    if not data:
        return None

    todos.write_todos(data.get("todos") or [])
    return data.get("messages")


def _title(messages: list) -> str:
    """The first thing the user actually asked, for telling sessions apart."""
    for message in messages:
        text = str(message.get("content") or "")
        if message.get("role") == "user" and not text.startswith("<env>"):
            return " ".join(text.split())[:60]
    return "(empty)"


def listing() -> list:
    """Sessions saved from this directory, newest first, as (name, count, title)."""
    here = str(Path.cwd())
    rows = []

    for file in DIR.glob("*.json"):
        data = _read(file)
        if not data or data.get("cwd") != here:
            continue
        messages = data.get("messages") or []
        rows.append((file.stat().st_mtime, file.stem, len(messages), _title(messages)))

    rows.sort(reverse=True)
    return [row[1:] for row in rows]


def latest() -> str | None:
    """The name of the most recent session saved from this directory."""
    rows = listing()
    return rows[0][0] if rows else None
