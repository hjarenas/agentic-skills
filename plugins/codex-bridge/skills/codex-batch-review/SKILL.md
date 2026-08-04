---
name: codex-batch-review
description: Independently review a scoped TRIP implementation batch and report evidenced findings without editing it
---

# Codex Batch Review

Run an independent, read-only delta review. Use a role-specific target such as
`<plan-path>#batch-review-2` so its stored report cannot collide with another bridge role.

Parse optional `--model`/`--effort`, the target, and trailing context. Run:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/codex-run.py <target> \
  --model <model-if-set> --effort <effort-if-set> \
  --prompt-file ${CLAUDE_PLUGIN_ROOT}/skills/codex-batch-review/prompts/review.tpl \
  --extra "<batch scope, plan path, prior staged baseline, and reviewer notes>"
```

Do not pass `--write`. Parse `BATCH_APPROVED` or `BATCH_REQUEST_FIXES`. Support `show` and
`reset` using the runtime flags. Surface the report verbatim to the orchestrator.
