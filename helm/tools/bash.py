import os
import shutil
import subprocess

MAX_CHARS = 30_000
DEFAULT_TIMEOUT = 60
MAX_TIMEOUT = 600

_BASH = shutil.which("bash")
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
