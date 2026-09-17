import sys
from pathlib import Path

from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style

HISTORY = Path.home() / ".helm" / "history"

STYLE = Style.from_dict({"prompt": "bold #9ece6a"})

bindings = KeyBindings()


@bindings.add("escape", "left")
def _word_left(event):
    buffer = event.current_buffer
    buffer.cursor_position += buffer.document.find_previous_word_beginning() or 0


@bindings.add("escape", "right")
def _word_right(event):
    buffer = event.current_buffer
    buffer.cursor_position += buffer.document.find_next_word_ending() or 0


@bindings.add("escape", "enter")
def _newline(event):
    event.current_buffer.insert_text("\n")


session = None


def read(prompt: str = "> ") -> str:
    """Read a line from the user. Raises EOFError on ctrl-d, like input()."""
    global session

    if session is None and sys.stdin.isatty():
        HISTORY.parent.mkdir(parents=True, exist_ok=True)
        session = PromptSession(
            history=FileHistory(str(HISTORY)),
            key_bindings=bindings,
            style=STYLE,
        )

    if session is None:
        return input(prompt)

    try:
        return session.prompt(HTML(f"<prompt>{prompt}</prompt>"))
    except (EOFError, KeyboardInterrupt):
        raise
    except Exception:
        session = None  # this terminal cannot host it, stop trying
        return input(prompt)
