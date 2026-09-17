# helm

A terminal coding agent. It reads and edits files, runs shell commands, and keeps
track of what it is doing across a conversation.

Works with any OpenAI-compatible chat completions endpoint.

## Setup

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
```

Create a `.env` in the project root:

```
BASE_URL=https://openrouter.ai/api/v1
API_KEY=sk-...
MODEL=deepseek/deepseek-v4-flash
```

`MODEL` is optional and defaults to `deepseek/deepseek-v4-flash`. A missing
`BASE_URL` or `API_KEY` fails at startup with a message rather than a traceback.

## Usage

```bash
uv run helm
```

| flag | effect |
| --- | --- |
| `--resume` | continue the most recent session from this directory |
| `--resume NAME` | continue a specific session |
| `--sessions` | list saved sessions for this directory and exit |

`alt-enter` inserts a newline, `ctrl-d` exits, `ctrl-c` aborts the current turn
without ending the session. Input history is kept in `~/.helm/history`.

## Tools

| tool | what it does |
| --- | --- |
| `bash` | run a shell command, with a timeout and closed stdin |
| `read_file` | read a file, returned with line numbers |
| `write_file` | create a file or fully replace one |
| `str_replace` | replace an exact substring, refusing ambiguous matches |
| `read_skill` | open a skill's full instructions |
| `write_todos` | replace the todo list |

## Permissions

Every tool call passes through `permissions.check()` before it runs.

`read_file`, `read_skill` and `write_todos` run without asking. So do read-only
bash commands (`git status`, `git diff`, `git log`, `ls`, `pwd`, `wc`) — but only
when nothing is chained onto them, so `ls; rm -rf .` still prompts.

Anything else asks:

```
run this?  y / a = always / n
```

`a` remembers that tool for the rest of the session. Anything other than `y` or
`a` declines, and the refusal goes back to the model as a normal tool result so
it can adapt instead of crashing.

## Sandbox

On macOS and Linux, bash commands are wrapped in an OS sandbox: no network, and
writes confined to the working directory with `.git` read only.

| platform | mechanism |
| --- | --- |
| macOS | `sandbox-exec` (Seatbelt) |
| Linux | `bwrap` (bubblewrap) |
| Windows | none — commands run unsandboxed |

There is no equivalent on Windows. Run helm under WSL2 or in a container if you
want the sandbox there.

## Skills

A skill is a folder holding a `SKILL.md` with YAML frontmatter:

```markdown
---
name: commit-message
description: Write a git commit message for the currently staged changes.
---

# Writing a commit message

1. Run `git diff --cached` to see what is actually staged.
...
```

Skills are read from `~/.agents/skills/` and `./.agents/skills/`, with the
project's copy winning on a name collision. Only the name and description go into
the system prompt; the agent calls `read_skill` to pull the full body when a task
matches. A malformed skill is skipped with a note at startup rather than taking
the agent down.

## Context

Once per turn, helm appends a block with the current state:

```
<env>
time: 2026-09-18 00:09
git branch: main

todos:
[x] read the config
[>] add the flag
[ ] run the tests

These files changed on disk since your last turn. Anything you read from them
earlier is out of date, so read them again before editing:
- config.py (modified)
</env>
```

File changes are detected by diffing `git status --porcelain` plus a content hash
of each changed file, so a second edit to an already-modified file is still
caught. It is injected once per turn rather than per step, which keeps the cached
prompt prefix stable.

## Sessions

Conversations are saved to `~/.helm/sessions/<timestamp>.json` after every turn,
along with the todo list. Each file records the directory it came from, so
`--resume` only offers sessions belonging to the project you are standing in.
Writes go to a temp file and are renamed into place, so a crash mid-save cannot
truncate an existing session.

## Layout

```
helm/
├── agent.py        the loop: call, run tools, repeat until the model answers
├── llm.py          the only module that talks to the API
├── system.py       system prompt assembly
├── context.py      the per-turn <env> block
├── permissions.py  the approval gate
├── sandbox.py      OS sandbox selection and command wrapping
├── skills.py       skill discovery and loading
├── session.py      save and resume
├── todos.py        the todo list
├── prompt.py       input line editing and history
├── ui.py           terminal rendering
├── config.py       environment
└── tools/
    ├── __init__.py tool schemas, registry, and dispatch
    ├── bash.py     shell detection and execution
    └── files.py    read, write, str_replace
```

The agent runs at most 25 steps per user turn. Each step is one API call, which
may carry several tool calls.
