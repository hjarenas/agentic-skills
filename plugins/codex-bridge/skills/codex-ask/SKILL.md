---
name: codex-ask
description: Ask Codex for a grounded second opinion on any question - advisory, not gating
argument-hint: "<topic-label> <question> | reset <topic-label> | show <topic-label>"
---

# Codex Ask

Free-form second opinion from Codex on **any matter** — architecture decisions, debugging
hypotheses, research conclusions, trade-off calls — not just plans and diffs. Codex answers from
inside the repository (read-only), so its opinion is grounded in the actual code, not in whatever
excerpt happened to be quoted.

**Advisory, not authoritative.** Unlike `codex-plan-review` / `codex-code-review`, there are no
verdict tags and nothing is gated on the answer: treat the response as one input to your judgment,
exactly like a colleague's opinion. Agreement is weak evidence; *disagreement* is a strong signal
that something deserves the user's attention.

Answers are stored per topic label under `.codex-bridge/` (gitignored) and spliced into follow-ups,
so a multi-round discussion holds together across stateless runs.

## Arguments

- `<topic-label>` — short kebab-case label for the discussion (becomes the state key), e.g. `orchestrator-choice`, `flaky-auth-test`. Auto: start if no stored answer, follow up if one exists.
- `<question>` — the actual question, passed as trailing text. Include your own draft position when you have one ("Here is my recommendation: … Red-team it").
- `reset <topic-label>` / `show <topic-label>` — drop the stored answer / display the last one.

## Execution

Let `RUN="python3 ${CLAUDE_PLUGIN_ROOT}/scripts/codex-run.py"` and
`P="${CLAUDE_PLUGIN_ROOT}/skills/codex-ask/prompts"`.

1. **Start** a discussion:
   ```bash
   $RUN <topic-label> --prompt-file $P/ask.tpl \
       --extra "<question — include your draft position and ask for disagreement>"
   ```

2. **Follow up** in the same discussion (counterpoints, new evidence):
   ```bash
   $RUN <topic-label> --prompt-file $P/followup.tpl --extra "<follow-up or counterpoint>"
   ```

3. **Reset**: `$RUN <topic-label> --prompt-file $P/ask.tpl --reset` — **Show**: same with `--show`

## When to use

- Second opinion on an architecture/design decision **before it hardens** (e.g., at the end of a research session, before writing the plan).
- Root-cause help when genuinely stuck on a bug — fresh eyes, different blind spots.
- "Red-team this conclusion" on a memo or recommendation you are about to present.

## When NOT to use

- Questions that need the **user's** preference or judgment — ask the user, not Codex.
- Trivial lookups or anything settled by reading the code yourself — every ask costs a Codex run.
- As a gate: never block or approve work based on the answer; that is what the review skills with verdict tags are for.
- Delegating actual work — that is `/codex:rescue` or `codex-implement`.

## Notes

- Read-only: no `--write`, so Codex can read the repo and change nothing.
- Surface Codex's answer to the user verbatim when it disagrees with your position — the
  disagreement itself is the valuable output.
