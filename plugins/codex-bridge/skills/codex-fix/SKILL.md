---
name: codex-fix
description: Apply scoped corrections requested by a TRIP reviewer and verify the corrected files
---

# Codex Fix

Apply only supplied findings. Use a unique target such as `<plan-path>#fix-batch-2-r1`.
Parse model/effort, target, and context, then invoke `codex-run.py` with `--write`, this skill's
`prompts/fix.tpl`, and findings in `--extra`. Never approve the fix or expand its scope.

Parse `FIX_COMPLETE` or `FIX_PARTIAL`; return the full report for independent re-review. Support
runtime `show` and `reset` actions.
