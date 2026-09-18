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
COMPACT_AT=700000
```

`MODEL` and `COMPACT_AT` are optional. A missing `BASE_URL` or `API_KEY` fails at
startup with a message rather than a traceback.

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
| `task` | hand a question to a subagent and get back only its answer |

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

## Subagents

The `task` tool runs a second agent with its own conversation, then hands the
parent only its final message. A search that costs thirty tool calls and several
whole files comes back as one paragraph, so the parent's context stays small.

A subagent gets `bash`, `read_file` and `read_skill` — no writing, and no `task`
of its own, so it cannot spawn more subagents. It runs for at most 15 steps, and
its tool calls go through the same permission gate as the parent's.

It cannot see the parent's conversation, so the question has to be self-contained.

## Compaction

When the prompt passes `COMPACT_AT` tokens, helm asks the model to summarise the
older part of the conversation and replaces it with those notes, keeping the
system prompt and the last 20 messages verbatim.

The cut point is never allowed to fall between an assistant message and its tool
results — that would make every later request invalid — so it moves forward to
the next user message or plain assistant reply.

Compaction only fires when both conditions hold: over the token threshold *and*
longer than the messages being kept. It rewrites the prefix, which discards the
prompt cache, so the threshold is deliberately high.

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
├── compact.py      summarising old history when it gets too long
├── subagent.py     running a nested agent for one question
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
