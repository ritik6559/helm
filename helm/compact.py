from .config import COMPACT_AT, MODEL
from .llm import client
from .ui import ui

KEEP = 20  # recent messages left verbatim

INSTRUCTION = """Summarise this conversation as notes to your future self.

Cover what the user asked for in their own terms, what you have already done
including the files you changed and commands you ran, what you learned about the
codebase that you would otherwise have to rediscover, and what is still
unfinished. Be specific about paths and names. No preamble."""


def _safe_cut(messages: list, start: int) -> int:
    """Move the cut forward until it lands where a request can legally begin."""
    while start < len(messages):
        message = messages[start]
        if message["role"] == "user":
            return start
        if message["role"] == "assistant" and not message.get("tool_calls"):
            return start
        start += 1
    return len(messages)


def compact(messages: list, used: int) -> list:
    """Replace old history with a summary once the prompt grows too large."""
    if used < COMPACT_AT:
        return messages

    cut = _safe_cut(messages, max(1, len(messages) - KEEP))
    old = messages[1:cut]
    if not old:
        return messages

    ui.notice("compacting history")

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=old + [{"role": "user", "content": INSTRUCTION}],
        )
    except Exception as e:
        ui.notice(f"could not compact: {e}")
        return messages

    summary = response.choices[0].message.content

    return [
        messages[0],
        {"role": "user", "content": f"<summary>\n{summary}\n</summary>"},
        *messages[cut:],
    ]
