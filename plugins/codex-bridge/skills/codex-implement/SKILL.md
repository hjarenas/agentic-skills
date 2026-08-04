---
name: codex-implement
description: Delegate implementation of a TRIP plan (or a scoped part of it) to Codex CLI
argument-hint: "[--model M] [--effort E] <plan-path> [instructions] | reset/show <plan-path>"
---

# Codex Implement

Delegate implementation to Codex with write access to the working tree: Codex reads the plan,
edits files directly, runs the project's lint/build on its own work, and reports back. A plan can
be delegated in successive batches (or phase by phase).

Unlike the review skills, this one **does** use the runtime's `--resume-last`, because continuing
the previous batch is the whole point and nothing else runs between batches. If you have run any
other Codex job in this workspace since the last batch, drop `--resume-last` and pass the context
through `--notes` instead — the runtime resumes the workspace's last thread, not this plan's.

Codex's report is stored at `.codex-bridge/<key>.md` (gitignored).

## Arguments

- `--model <model>` / `--effort <effort>` — optional per-run runtime overrides. Remove them
  before parsing the action and target.
- `<target>` — usually a plan path (`docs/1-plans/F_*.plan.md`); a free-form label for unplanned work.
- Optional trailing instructions — scope control, e.g. `"Implement only: <batch checkboxes>"` or `"Now implement: <next batch>"`.
- `reset <target>` — drop the stored report, next call starts fresh.
- `show <target>` — display the latest report without calling Codex.

## Execution

Let `RUN="python3 ${CLAUDE_PLUGIN_ROOT}/scripts/codex-run.py"` and
`P="${CLAUDE_PLUGIN_ROOT}/skills/codex-implement/prompts"`.

1. **Parse `$ARGUMENTS`**: extract optional model/effort, action (`reset`/`show`/auto), and
   target. Build `MODEL_ARGS` as the present runtime flags.

2. **Auto**:
   - **Start** (no stored report): `$RUN <target> $MODEL_ARGS --write --prompt-file $P/implement.tpl --extra "<scope instructions>"`
   - **Resume** (next batch): `$RUN <target> $MODEL_ARGS --write --resume-last --prompt-file $P/continue.tpl --notes "<what you fixed after the last batch and why>" --extra "<next batch>"`

3. **Reset**: `$RUN <target> --prompt-file $P/implement.tpl --reset`

4. **Show**: `$RUN <target> --prompt-file $P/implement.tpl --show`

5. **Parse trailing tag** of the report:
   - `IMPLEMENTATION_COMPLETE` — hand control back to the requester's batch review (TRIP-2).
   - `IMPLEMENTATION_PARTIAL` — read the report; resume with instructions for the remainder, or let the requester finish small leftovers directly.

For a long batch, add `--background` and poll with `/codex:status`, collecting the result with
`/codex:result`.

## Notes

- **Fixes are the requester's job.** After Codex reports, the requester (TRIP-2 batch review) fixes
  problems directly in the tree — do NOT ping-pong fixes back to Codex. Resume only for genuinely
  new scope (next batch, large remainder), passing what was fixed and why via `--notes`.
- Codex is instructed not to write tests (the testing gate owns that) and not to touch release ceremony.
- `--write` maps to the runtime's write-capable mode. Network access follows the Codex plugin's own
  sandbox settings; if the plan needs a new dependency, expect it as a reported leftover and install
  it yourself during the batch review.
- Model/effort follow `.codex/config.toml`. Override per run with `--model` / `--effort` (e.g. a
  stronger model for implementation than for review), or via `CODEX_MODEL` / `CODEX_EFFORT`.
