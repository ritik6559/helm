import json

from .files import read_file, write_file

TOOL_SCHEMAS = [
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
