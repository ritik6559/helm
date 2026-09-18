import json

from ..skills import read_skill
from ..subagent import task
from ..todos import write_todos

from .bash import DEFAULT_TIMEOUT, MAX_TIMEOUT, SHELL_NAME, bash
from .files import read_file, str_replace, write_file
from ..permissions import check
from ..subagent import task

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "bash",
            "description": (
                f"Run a command in {SHELL_NAME} from the current working directory. "
                "Returns stdout and stderr combined, prefixed with the exit code when "
                "the command fails. Use this for running tests, git, and inspecting the "
                "project. Prefer read_file and write_file for reading and editing file "
                "contents. stdin is closed, so never run a command that waits for input, "
                "and never start a long-running server."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The command to run.",
                    },
                    "timeout": {
                        "type": "integer",
                        "description": (
                            f"Seconds to wait before the command is killed. "
                            f"Defaults to {DEFAULT_TIMEOUT}, maximum {MAX_TIMEOUT}."
                        ),
                    },
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": (
                "Read a text file from disk. Returns the contents with 1-indexed "
                "line numbers prefixed to each line."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file, relative to the current directory.",
                    },
                    "offset": {
                        "type": "integer",
                        "description": "0-indexed line to start from. Defaults to the start of the file.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of lines to read. Defaults to the whole file.",
                    },
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": (
                "Write content to a file, replacing it entirely if it already exists. "
                "Creates parent directories as needed. Read the file first before "
                "overwriting one that already exists."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file, relative to the current directory.",
                    },
                    "content": {
                        "type": "string",
                        "description": "The full contents to write. Do not include line numbers.",
                    },
                },
                "required": ["path", "content"],
            },
        },
    },
]

TOOL_SCHEMAS += [
    {
        "type": "function",
        "function": {
            "name": "str_replace",
            "description": (
                "Replace an exact substring in a file. This is the preferred way to edit "
                "an existing file, because everything outside old_string is left untouched. "
                "old_string must match the file byte for byte including indentation, must "
                "not carry the line numbers read_file adds, and must appear exactly once "
                "unless replace_all is true."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file, relative to the current directory.",
                    },
                    "old_string": {
                        "type": "string",
                        "description": "The exact text to find, with enough context to be unique.",
                    },
                    "new_string": {
                        "type": "string",
                        "description": "The text to put in its place.",
                    },
                    "replace_all": {
                        "type": "boolean",
                        "description": "Replace every occurrence instead of requiring a unique match.",
                    },
                },
                "required": ["path", "old_string", "new_string"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_skill",
            "description": (
                "Open a skill by name and return its full instructions. The available "
                "skills are listed in your system prompt with a one line summary each. "
                "Read the whole skill before starting work it applies to."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The skill name exactly as listed in the system prompt.",
                    },
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_todos",
            "description": (
                "Replace your todo list. Use it for tasks that take several steps: "
                "write the plan out first, then call this again as each item finishes. "
                "Always send the whole list, not just the part that changed. The current "
                "list is shown back to you every turn."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "todos": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "task": {
                                    "type": "string",
                                    "description": "What needs doing, in a few words.",
                                },
                                "status": {
                                    "type": "string",
                                    "enum": ["pending", "doing", "done"],
                                },
                            },
                            "required": ["task", "status"],
                        },
                    },
                },
                "required": ["todos"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "task",
            "description": (
                "Hand one self-contained question to a fresh agent with its own "
                "context, and get back only its answer. Use it for searches that would "
                "otherwise fill your context with file contents you do not need to "
                "keep, such as finding where something is defined or tracing how a "
                "feature works across several files. The subagent cannot edit "
                "anything and cannot ask you questions, so put everything it needs "
                "into the question."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": (
                            "The full question, with enough context to answer it "
                            "without seeing this conversation."
                        ),
                    },
                },
                "required": ["question"],
            },
        },
    }
]

TOOLS = {
    "bash": bash,
    "read_file": read_file,
    "read_skill": read_skill,
    "str_replace": str_replace,
    "write_file": write_file,
    "write_todos": write_todos,
    "task": task
}


def execute(tool_call) -> dict:
    """Run one tool call and return the tool-role message to append to history."""
    name = tool_call.function.name
    fn = TOOLS.get(name)

    if fn is None:
        result = f"Error: unknown tool {name!r}. Available tools: {', '.join(TOOLS)}."
    else:
        try:
            args = json.loads(tool_call.function.arguments or "{}")
            denied = check(name, args)
            result = denied if denied else fn(**args)
        except json.JSONDecodeError as e:
            result = f"Error: could not parse arguments for {name}: {e}"
        except TypeError as e:
            result = f"Error: bad arguments for {name}: {e}"
        except Exception as e:
            result = f"Error: {name} failed: {type(e).__name__}: {e}"

    return {
        "role": "tool",
        "tool_call_id": tool_call.id,
        "content": result,
    }
