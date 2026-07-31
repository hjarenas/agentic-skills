---
name: codex-plan-review
description: Iterative Codex CLI review of a planning document
argument-hint: "<plan-path> [extra context] | reset <plan-path> | show <plan-path>"
---

# Codex Plan Review

Iterative review of a planning document via Codex, using TRIP's own review prompt.

There is deliberately no `/codex:*` equivalent for this: `/codex:review` and
`/codex:adversarial-review` are both git-diff scoped and cannot review a markdown plan. This
skill runs TRIP's prompt through the same Codex runtime that the `codex` plugin installs.

Each turn is a **fresh Codex run**. The runtime can only resume the workspace's *last* thread,
which would collide with the implement/review alternation in TRIP-2, so the loop state travels
in the prompt instead: the previous review is stored under `.codex-bridge/` (gitignored) and
spliced back in as the prompt's prior-review block.

## Arguments

- `<plan-path>` — auto: start if no stored review, resume if one exists. Trailing free-text is extra context.
- `reset <plan-path>` — drop the stored review, next call starts fresh.
- `show <plan-path>` — display the latest review without calling Codex.

## Execution

Let `RUN="python3 ${CLAUDE_PLUGIN_ROOT}/scripts/codex-run.py"` and
`P="${CLAUDE_PLUGIN_ROOT}/skills/codex-plan-review/prompts"`.

1. **Parse `$ARGUMENTS`**: extract action (`reset`/`show`/auto) and plan path.

2. **Auto** — a stored review exists if `.codex-bridge/<key>.md` is present; `--show` failing is
   the simplest check.
   - **Start** (no stored review): `$RUN <plan-path> --prompt-file $P/start.tpl --extra "<extra>"`
   - **Resume** (stored review exists): `$RUN <plan-path> --prompt-file $P/resume.tpl --notes "<what you changed and why>" --extra "<extra>"`

3. **Reset**: `$RUN <plan-path> --prompt-file $P/start.tpl --reset`

4. **Show**: `$RUN <plan-path> --prompt-file $P/start.tpl --show`

5. **Parse trailing tag**:
   - `APPROVED` — tell user, done.
   - `REQUEST_CHANGES` — engage critically: fix legitimate findings by editing the plan, push back on incorrect ones. Surface review verbatim, propose fixes, let user confirm.
   - `NEEDS_REWORK` — surface to user before mass-editing.

## Notes

- Always pass `--notes` on resume. Because the run is stateless, the notes are the only signal
  that distinguishes "I fixed this" from "I disagree, and here is why" — without them Codex
  re-raises findings you already settled.
- Read-only: no `--write` flag, so Codex inspects the repo and changes nothing.
- Model/effort follow the Codex plugin's own config (`.codex/config.toml`). Override per run with
  `--model` / `--effort`, or by exporting `CODEX_MODEL` / `CODEX_EFFORT`.
- Requires the `codex` plugin (declared as a dependency). If the runner cannot find it, it prints
  the exact `/plugin` commands to run.

## Loop Shape

```
turn 1: start.tpl  -> REQUEST_CHANGES (A B C)
         address A B C
turn 2: resume.tpl -> REQUEST_CHANGES (A B addressed, C stale, new D)
         address C D
turn 3: resume.tpl -> APPROVED
```
