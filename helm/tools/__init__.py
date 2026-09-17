import json

from .bash import DEFAULT_TIMEOUT, MAX_TIMEOUT, SHELL_NAME, bash
from .files import read_file, write_file

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

TOOLS = {
    "bash": bash,
    "read_file": read_file,
    "write_file": write_file,
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
            result = fn(**args)
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
