import hashlib
import subprocess
from datetime import datetime
from pathlib import Path

HASH_LIMIT = 10 * 1024 * 1024

LABELS = {
    "M": "modified",
    "A": "added",
    "D": "deleted",
    "R": "renamed",
    "C": "copied",
    "U": "conflicted",
    "?": "untracked",
}

_LAST_STATE = None


def _git_raw(*args) -> str | None:
    """Run a git command, or return None if git is missing or this is not a repo."""
    try:
        result = subprocess.run(
            ["git", *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdin=subprocess.DEVNULL,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None

    if result.returncode != 0:
        return None
    return result.stdout


def _git(*args) -> str | None:
    out = _git_raw(*args)
    return None if out is None else out.strip()


def git_branch() -> str | None:
    branch = _git("branch", "--show-current")
    if branch is None:
        return None
    return branch or "(detached)"


def _fingerprint(path: Path) -> str | None:
    """A cheap content identity for a file, or None if it cannot be read."""
    try:
        size = path.stat().st_size
        if size > HASH_LIMIT:
            return f"size:{size}"

        digest = hashlib.md5()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(65536), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError:
        return None


def _label(code: str) -> str:
    for char in code:
        if char in LABELS:
            return LABELS[char]
    return "changed"


def git_state() -> dict | None:
    """Map every path git considers changed to (status code, content fingerprint)."""
    out = _git_raw("status", "--porcelain", "-z")
    if out is None:
        return None

    root = _git("rev-parse", "--show-toplevel")
    if root is None:
        return None
    base = Path(root)

    state = {}
    entries = out.split("\0")
    index = 0

    while index < len(entries):
        entry = entries[index]
        index += 1
        if len(entry) < 4:
            continue

        code, path = entry[:2], entry[3:]
        if code[0] in "RC":
            index += 1 

        state[path] = (code, _fingerprint(base / path))

    return state


def file_changes() -> dict:
    """Paths that changed since the last snapshot, as {path: label}."""
    global _LAST_STATE

    current = git_state()
    if current is None:
        return {}

    previous, _LAST_STATE = _LAST_STATE, current
    if previous is None:
        return {}  

    changes = {
        path: _label(entry[0])
        for path, entry in current.items()
        if previous.get(path) != entry
    }
    for path in previous:
        if path not in current:
            changes[path] = "reverted or committed"

    return changes


def refresh() -> None:
    """Re-baseline once the agent finishes, so its own edits are not reported back."""
    global _LAST_STATE
    state = git_state()
    if state is not None:
        _LAST_STATE = state


def changes_note(changes: dict) -> str:
    if not changes:
        return ""

    listing = "\n".join(f"- {path} ({label})" for path, label in sorted(changes.items()))
    return (
        "These files changed on disk since your last turn. Anything you read from "
        f"them earlier is out of date, so read them again before editing:\n{listing}"
    )


def reminder() -> dict:
    """The block we append to the messages once per user turn."""
    lines = [f"time: {datetime.now():%Y-%m-%d %H:%M}"]

    branch = git_branch()
    if branch:
        lines.append(f"git branch: {branch}")

    body = "\n".join(lines)
    note = changes_note(file_changes())
    if note:
        body = f"{body}\n\n{note}"

    return {"role": "user", "content": f"<env>\n{body}\n</env>"}
