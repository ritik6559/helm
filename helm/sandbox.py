import shutil
import sys
import tempfile
from pathlib import Path

PROJECT = Path.cwd().resolve()

PROFILE = f"""(version 1)
(allow default)
(deny network*)
(deny file-write*)
(allow file-write*
    (subpath "{PROJECT}")
    (subpath "/private/tmp")
    (subpath "/private/var/folders")
    (literal "/dev/null")
    (literal "/dev/tty"))
(deny file-write* (subpath "{PROJECT / ".git"}"))
"""


def _seatbelt(command: str) -> list:
    profile = Path(tempfile.gettempdir()) / "helm.sb"
    profile.write_text(PROFILE, encoding="utf-8")
    return ["sandbox-exec", "-f", str(profile), "/bin/sh", "-c", command]


def _bubblewrap(command: str) -> list:
    args = [
        "bwrap",
        "--ro-bind", "/", "/",
        "--bind", str(PROJECT), str(PROJECT),
    ]

    git = PROJECT / ".git"
    if git.exists():
        args += ["--ro-bind", str(git), str(git)]

    return args + [
        "--dev", "/dev",
        "--proc", "/proc",
        "--tmpfs", "/tmp",
        "--unshare-net",
        "/bin/sh", "-c", command,
    ]


def _pick():
    if sys.platform == "darwin" and shutil.which("sandbox-exec"):
        return "seatbelt", _seatbelt
    if sys.platform.startswith("linux") and shutil.which("bwrap"):
        return "bubblewrap", _bubblewrap
    return "none", None


NAME, _wrap = _pick()


def wrap(command: str) -> list | None:
    """The command re-wrapped in an OS sandbox, or None if there is none here."""
    return _wrap(command) if _wrap else None
