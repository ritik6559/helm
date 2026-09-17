import os
import shutil
import subprocess
from pathlib import Path

MAX_CHARS = 30_000
DEFAULT_TIMEOUT = 60
MAX_TIMEOUT = 600


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


_BASH = _find_bash()
SHELL_NAME = "bash" if _BASH else ("cmd.exe" if os.name == "nt" else "sh")


def _truncate(output: str) -> str:
    output = output.strip()
    if len(output) <= MAX_CHARS:
        return output
    return f"{output[:MAX_CHARS]}\n... truncated at {MAX_CHARS} characters ..."


def bash(command: str, timeout: int = DEFAULT_TIMEOUT) -> str:
    """Run a shell command and return its combined output."""
    if not command or not command.strip():
        return "Error: command is empty."

    try:
        timeout = max(1, min(int(timeout), MAX_TIMEOUT))
    except (TypeError, ValueError):
        timeout = DEFAULT_TIMEOUT

    args = [_BASH, "-c", command] if _BASH else command

    try:
        completed = subprocess.run(
            args,
            shell=not _BASH,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as e:
        partial = _truncate(e.output or "")
        killed = f"Error: command exceeded {timeout}s and was killed."
        return f"{killed}\nOutput before the timeout:\n{partial}" if partial else killed
    except OSError as e:
        return f"Error: could not run command: {e}"

    output = _truncate(completed.stdout or "")

    if completed.returncode != 0:
        return f"exit code {completed.returncode}\n{output}" if output else f"exit code {completed.returncode} (no output)"

    return output or "(no output)"
