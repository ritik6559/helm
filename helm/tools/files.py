from pathlib import Path

MAX_CHARS = 100_000


def read_file(path: str, offset: int = 0, limit: int | None = None) -> str:
    """Read a text file, returning its lines with 1-indexed numbers."""
    
    file = Path(path)
    if not file.exists():
        return f"Error: {path} does not exist."
    if file.is_dir():
        return f"Error: {path} is a directory, not a file."

    try:
        content = file.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return f"Error: {path} is not a UTF-8 text file."
    except OSError as e:
        return f"Error reading {path}: {e}"

    lines = content.splitlines()
    selected = lines[offset:] if limit is None else lines[offset : offset + limit]
    if not selected:
        return f"{path} is empty." if not lines else f"Error: offset {offset} is past the end of {path} ({len(lines)} lines)."

    numbered = "\n".join(
        f"{i}\t{line}" for i, line in enumerate(selected, start=offset + 1)
    )
    if len(numbered) > MAX_CHARS:
        numbered = numbered[:MAX_CHARS] + f"\n... truncated at {MAX_CHARS} characters, use offset to read further ..."
    return numbered

def write_file(path: str, content: str) -> str:
    """Write content to a file, creating parent directories as needed."""
    file = Path(path)
    existed = file.exists()
    if file.is_dir():
        return f"Error: {path} is a directory, not a file."

    try:
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(content, encoding="utf-8")
    except OSError as e:
        return f"Error writing {path}: {e}"

    action = "Updated" if existed else "Created"
    return f"{action} {path} ({len(content.splitlines())} lines)."
