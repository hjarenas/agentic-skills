---
name: codex-code-review
description: Iterative Codex CLI code review against an implementation plan
argument-hint: "[--model M] [--effort E] <plan-path> [extra context] | reset/show <plan-path>"
---

# Codex Code Review

Iterative code review of uncommitted changes via Codex, using TRIP's own review prompt. Codex
reads the plan and runs `git status -s` / `git diff HEAD` to inspect the change set.

## Why not `/codex:review`?

`/codex:review` is a good pass and worth running too, but it is not a substitute here. It ships
OpenAI's own prompt and emits a two-state verdict (`approve` / `needs-attention`), reviewing the
diff cold. This skill's prompt is grounded in `docs/archi/` and the project-local
`docs/3-code-review/checklist.md`, suppresses the false-positive classes TRIP cares about
(doc-compliance nits, theoretical edge cases, findings the implementer already settled), and
emits the three-state verdict TRIP-2 branches on.

Use `/codex:adversarial-review` as an *additional* pass when a change is risky — it attacks the
design rather than the implementation, which neither this skill nor `/codex:review` does.

Each turn is a **fresh Codex run**; the previous review is stored under `.codex-bridge/`
(gitignored) and spliced back into the prompt. Review output stays there — promotion to
`docs/3-code-review/CR_wa_vx.y.z.md` happens after convergence, not per turn.

## Arguments

- `--model <model>` / `--effort <effort>` — optional per-run runtime overrides. Remove them
  before parsing the action and target.
- `<target>` — auto: start if no stored review, resume if one exists. Usually a plan path (`docs/1-plans/F_*.plan.md`) or a free-form label for unplanned work.
- `reset <target>` — drop the stored review, next call starts fresh.
- `show <target>` — display the latest review without calling Codex.

## Execution

Let `RUN="python3 ${CLAUDE_PLUGIN_ROOT}/scripts/codex-run.py"` and
`P="${CLAUDE_PLUGIN_ROOT}/skills/codex-code-review/prompts"`.

1. **Parse `$ARGUMENTS`**: extract optional model/effort, action (`reset`/`show`/auto), and
   target. Build `MODEL_ARGS` as the present runtime flags.

2. **Auto**:
   - **Start**: `$RUN <target> $MODEL_ARGS --prompt-file $P/start.tpl --extra "<lint/typecheck/test summary + intent>"`
   - **Resume**: `$RUN <target> $MODEL_ARGS --prompt-file $P/resume.tpl --notes "<what you fixed, what you pushed back on and why>" --extra "<extra>"`

3. **Reset**: `$RUN <target> --prompt-file $P/start.tpl --reset`

4. **Show**: `$RUN <target> --prompt-file $P/start.tpl --show`

5. **Parse trailing tag**:
   - `APPROVED` — propose post-convergence steps.
   - `REQUEST_CHANGES` — surface review verbatim, engage critically (read actual code at `file:line`, fix legitimate ones, push back on incorrect ones), then resume.
   - `NEEDS_REWORK` — surface to user before mass-editing.

6. **Resume** after addressing findings for incremental re-review.

## Diff Visibility

Codex runs read-only. If `git status -s` / `git diff HEAD` fail for it, pass the diff inline as
extra context: `DIFF="$(git diff --stat HEAD; echo '---'; git diff HEAD)"`.

## After Convergence

1. Produce the consolidated review: `$RUN <target> --prompt-file $P/synthesize.tpl --extra "<round-by-round summary>"`
2. Write it to `docs/3-code-review/CR_wa_vx.y.z.md`.
3. Continue with `TRIP-3-release`.

## Notes

- Always pass `--notes` on resume — a stateless run has no other way to know which findings you
  settled and which you rejected.
- Read-only sandbox. Safe to invoke autonomously.
- The `.codex-bridge/` key is derived from the target, so a plan's code review and its plan
  review do not overwrite each other.

## Loop Shape

```
turn 1: start.tpl  -> REQUEST_CHANGES (Critical: A, Major: B C)
         address A B C
turn 2: resume.tpl -> REQUEST_CHANGES (A B addressed, Minor: C partial, Suggestion: D)
         address C, optionally D
turn 3: resume.tpl -> APPROVED -> synthesize, promote, continue with TRIP-3-release
```
