from .ui import ui

SAFE = ["read_file", "read_skill", "write_todos"]

SAFE_COMMANDS = ("git status", "git diff", "git log", "ls", "pwd", "wc")
CHAINS = (";", "&&", "||", "|", ">", "<", "`", "$(")

_always = set()

def _safe_command(args: dict) -> bool:
    command = str(args.get("command", "")).strip()
    if any(chain in command for chain in CHAINS):
        return False
    return command.startswith(SAFE_COMMANDS)

def check(name: str, args: dict) -> str | None:
    """Return None to run the tool, or the message to send back instead"""
    if name in SAFE or name in _always:
        return None 
    if name == "bash" and _safe_command(args):
        return None

    answer = ui.confirm(name, args)
    if answer == "always":
        _always.add(name)
    if answer in ["yes", "always"]:
        return None
    
    return f"Error: the user declines to run {name}"