---
name: codex-workspace
description: Perform narrowly authorized TRIP git workspace operations such as branch selection, staging, commit, push, and status reporting
---

# Codex Workspace Worker

Use a unique target such as `<plan-path>#workspace-branch`. Parse model/effort and invoke
`codex-run.py` with `--write`, `prompts/workspace.tpl`, and an exact allowlist of operations in
`--extra`.

This skill does not grant authority by itself. Do not infer permission for stashing, deletion,
force operations, merging, tagging, or unrelated commits. Parse `WORKSPACE_COMPLETE` or
`WORKSPACE_BLOCKED`. Support runtime `show` and `reset` actions.
