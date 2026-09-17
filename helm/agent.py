import json

from .skills import SKILL_ERRORS
from .system import system_prompt
from .llm import call_llm
from .tools import execute
from .ui import ui

MAX_STEPS_PER_TURN = 25

def _parse_args(raw: str) -> dict:
    """Decode tool arguments for display, tolerating whatever the model emitted."""
    try:
        args = json.loads(raw or "{}")
    except json.JSONDecodeError:
        return {"raw": raw}
    return args if isinstance(args, dict) else {"raw": raw}

def run_turn(messages: list) -> None:
    """Step until the model answers without calling a tool, or the cap is hit."""
    for _ in range(MAX_STEPS_PER_TURN):
        with ui.working():
            message, usage = call_llm(messages)

        messages.append(message.model_dump(exclude_none=True))

        if message.content:
            ui.agent(message.content)

        ui.usage(usage)

        if not message.tool_calls:
            return

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

def main() -> None:
    messages = [{"role": "system", "content": system_prompt()}]
    ui.banner()

    for error in SKILL_ERRORS:
        ui.notice(f"skipped skill - {error}")

    while True:
        user_input = ui.ask()

        if user_input is None or user_input in {"/exit", "/quit"}:
            break
        if not user_input:
            continue

        messages.append({"role": "user", "content": user_input})

        try:
            run_turn(messages)
        except KeyboardInterrupt:
            ui.notice("interrupted")

    ui.summary()

if __name__ == "__main__":
    main()
