import os
import shutil
import subprocess
from pathlib import Path


def _runs(path: str) -> bool:
    """Confirm a candidate really is a working shell."""
    try:
        completed = subprocess.run(
            [path, "-c", "exit 0"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return completed.returncode == 0


def _candidates() -> list:
    if os.name != "nt":
        return [shutil.which("bash")]

    paths = []
    if os.environ.get("SHELL"):
        paths.append(os.environ["SHELL"])

    for key in ("ProgramFiles", "ProgramW6432", "ProgramFiles(x86)", "LOCALAPPDATA"):
        root = os.environ.get(key)
        if root:
            paths.append(str(Path(root) / "Git" / "bin" / "bash.exe"))

    paths.append(shutil.which("bash"))
    return paths


def _find_bash() -> str | None:
    """Locate a real bash. On Windows, PATH order often puts the WSL launcher
    at C:\\Windows\\System32\\bash.exe first, which fails when WSL is absent."""
    system_root = Path(os.environ.get("SystemRoot", r"C:\Windows"))

    seen = set()
    for candidate in _candidates():
        if not candidate:
            continue
        try:
            resolved = Path(candidate).resolve()
        except OSError:
            continue

        key = str(resolved).lower()
        if key in seen:
            continue
        seen.add(key)

        if not resolved.is_file():
            continue
        if os.name == "nt" and system_root.resolve() in resolved.parents:
            continue
        if _runs(str(resolved)):
            return str(resolved)

    return None


BASH = _find_bash()
SHELL_NAME = "bash" if BASH else ("cmd.exe" if os.name == "nt" else "sh")
