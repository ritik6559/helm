import argparse
import json

from . import session
from .compact import compact
from .skills import SKILL_ERRORS
from .system import system_prompt
from .llm import call_llm
from .tools import TOOL_SCHEMAS, execute
from .ui import ui
from .context import refresh, reminder

MAX_STEPS_PER_TURN = 25

def _parse_args(raw: str) -> dict:
    """Decode tool arguments for display, tolerating whatever the model emitted."""
    try:
        args = json.loads(raw or "{}")
    except json.JSONDecodeError:
        return {"raw": raw}
    return args if isinstance(args, dict) else {"raw": raw}

def run_turn(messages: list) -> int:
    """Step until the model answers or the cap is hit. Returns the last prompt size."""
    used = 0

    for _ in range(MAX_STEPS_PER_TURN):
        with ui.working():
            message, usage = call_llm(messages, TOOL_SCHEMAS)

        messages.append(message.model_dump(exclude_none=True))

        if message.content:
            ui.agent(message.content)

        ui.usage(usage)
        used = usage.get("prompt_tokens") or 0

        if not message.tool_calls:
            return used

        for index, tool_call in enumerate(message.tool_calls):
            try:
                result = execute(tool_call)
            except KeyboardInterrupt:
                for pending in message.tool_calls[index:]:
                    messages.append({
                        "role": "tool",
                        "tool_call_id": pending.id,
                        "content": "Error: interrupted by the user.",
                    })
                raise
            ui.tool(
                tool_call.function.name,
                _parse_args(tool_call.function.arguments),
                result["content"],
            )
            messages.append(result)

    ui.notice(f"stopped after {MAX_STEPS_PER_TURN} steps - say 'continue' to keep going")
    return used

def parse_args():
    parser = argparse.ArgumentParser(prog="helm", description="A terminal coding agent.")
    parser.add_argument(
        "--resume",
        nargs="?",
        const="",
        metavar="NAME",
        help="continue a session: the most recent one, or NAME from --sessions",
    )
    parser.add_argument(
        "--sessions",
        action="store_true",
        help="list saved sessions for this directory and exit",
    )
    return parser.parse_args()


def start(resume: str | None) -> tuple:
    """Resume a session for this directory, or begin a new one."""
    if resume is not None:
        name = resume or session.latest()
        messages = session.load(name) if name else None
        if messages:
            messages[0] = {"role": "system", "content": system_prompt()}
            return name, messages
        ui.notice("no session to resume here, starting a new one")

    return session.new_name(), [{"role": "system", "content": system_prompt()}]


def main() -> None:
    args = parse_args()
    ui.banner()

    if args.sessions:
        rows = session.listing()
        for name, count, title in rows:
            ui.notice(f"{name}  {count:>3} msgs  {title}")
        if not rows:
            ui.notice("no sessions saved from this directory")
        return

    name, messages = start(args.resume)

    for error in SKILL_ERRORS:
        ui.notice(f"skipped skill - {error}")

    if len(messages) > 1:
        ui.notice(f"resumed {name} with {len(messages) - 1} messages")

    while True:
        user_input = ui.ask()

        if user_input is None or user_input in {"/exit", "/quit"}:
            break
        if not user_input:
            continue

        messages.append(reminder())
        messages.append({"role": "user", "content": user_input})

        used = 0
        try:
            used = run_turn(messages)
        except KeyboardInterrupt:
            ui.notice("interrupted")
        finally:
            refresh()
            messages[:] = compact(messages, used)
            session.save(name, messages)

    ui.summary()

if __name__ == "__main__":
    main()
