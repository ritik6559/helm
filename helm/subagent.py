from .llm import call_llm
from .system import system_prompt
from .ui import ui

MAX_STEPS = 15

ALLOWED = {"bash", "read_file", "read_skill"}

PROMPT = """You are a subagent. The main agent has given you one question and you
answer that question, nothing else.

You cannot ask for clarification, and nobody will read anything except your final
message, so make that message complete on its own. Quote the file paths, line
numbers and command output that support your answer. If you could not find out,
say so plainly rather than guessing."""


def task(question: str) -> str:
    """Run a fresh agent on one question and return only its answer."""
    # Deferred: tools imports this module to register the task tool.
    from .tools import TOOL_SCHEMAS, execute

    tools = [t for t in TOOL_SCHEMAS if t["function"]["name"] in ALLOWED]
    messages = [
        {"role": "system", "content": f"{system_prompt(delegate=False)}\n\n{PROMPT}"},
        {"role": "user", "content": question},
    ]

    ui.notice(f"subagent: {question}")

    for _ in range(MAX_STEPS):
        message, _ = call_llm(messages, tools)
        messages.append(message.model_dump(exclude_none=True))

        if not message.tool_calls:
            return message.content or "The subagent returned no answer."

        for call in message.tool_calls:
            result = execute(call)
            ui.tool(
                f"subagent {call.function.name}",
                {"args": call.function.arguments},
                result["content"],
            )
            messages.append(result)

    return f"The subagent used all {MAX_STEPS} steps without reaching an answer."
