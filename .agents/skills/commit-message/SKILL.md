---
name: commit-message
description: Write a git commit message for the currently staged changes. Use when asked to commit, or to write or fix a commit message.
---

# Writing a commit message

1. Run `git diff --cached` to see what is actually staged. If nothing is staged,
   say so and stop rather than staging files yourself.
2. Run `git log -5 --format=%s` and match the style already in the repository —
   prefixes, capitalisation, and mood.

## Format

- A subject line under 72 characters, in the imperative mood: "Add retry to the
  upload path", never "Added" or "Adds".
- No trailing period on the subject.
- If the change needs explanation, add a blank line then a body that says **why**
  the change was made. The diff already shows what changed.
- One logical change per commit. If the staged diff covers several unrelated
  changes, say so and suggest splitting it.

## Do not

- Do not run `git commit` unless you were explicitly asked to commit.
- Do not mention the tools you used to inspect the diff.
