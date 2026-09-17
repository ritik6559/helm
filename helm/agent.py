from system import system_prompt
from llm import call_llm
from tools import execute

MAX_STEPS_PER_TURN = 25


def _preview(text: str, limit: int = 200) -> str:
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return f"{text[:limit]} ... (+{len(text) - limit} chars)"


def run_turn(messages: list) -> None:
    """Step until the model answers without calling a tool, or the cap is hit."""
    
    for step in range(1, MAX_STEPS_PER_TURN + 1):
        message, usage = call_llm(messages)
        messages.append(message.model_dump(exclude_none=True))

        if message.content:
            print(f"\nAgent: {message.content}\n")

        print(f"[step {step}] {usage}")

        if not message.tool_calls:
            return

        for index, tool_call in enumerate(message.tool_calls):
            print(f"  -> {tool_call.function.name}({_preview(tool_call.function.arguments)})")
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
            print(f"     {_preview(result['content'])}")
            messages.append(result)

    print(f"\nStopped after {MAX_STEPS_PER_TURN} steps without finishing. Say 'continue' to keep going.")


def main() -> None:
    messages = [{"role": "system", "content": system_prompt()}]
    print("helm - /exit or Ctrl+D to quit, Ctrl+C to abort a turn")

    while True:
        try:
            user_input = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return

        if not user_input:
            continue
        if user_input in {"/exit", "/quit"}:
            return

        messages.append({"role": "user", "content": user_input})

        try:
            run_turn(messages)
        except KeyboardInterrupt:
            print("\n[interrupted]")


if __name__ == "__main__":
    main()
