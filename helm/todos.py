TODOS = []

MARKS = {"pending": " ", "doing": ">", "done": "x"}


def write_todos(todos: list) -> str:
    """Replace the todo list."""
    global TODOS

    if not isinstance(todos, list):
        return "Error: todos must be a list."

    TODOS = [t for t in todos if isinstance(t, dict) and t.get("task")]
    return todos_prompt() or "Todo list cleared."


def todos_prompt() -> str:
    return "\n".join(
        f"[{MARKS.get(t.get('status'), ' ')}] {t['task']}" for t in TODOS
    )
