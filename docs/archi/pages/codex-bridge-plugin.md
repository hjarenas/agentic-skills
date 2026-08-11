---
title: codex-bridge plugin
status: current
updated: 2026-08-11
verified-at: 1.2.1
links: [distribution, trip-plugin]
---

Nine worker-role skills that run prompts through OpenAI's Codex CLI (installed separately as the
`openai-codex` marketplace's `codex` plugin, a declared dependency) and report back a typed
verdict tag. [[trip-plugin]] dispatches these as its `codex-bridge`-harness workers; they can also
be invoked directly. See [[distribution]] for how a plugin dependency across two marketplaces
gets installed.

## Every role is stateless

Each turn is a fresh Codex process with no memory of earlier turns — a Codex-side constraint, not
a design choice. Continuity travels only through `--notes` (what was fixed, what was disputed and
why) and a stored report the harness splices back into the next prompt as context. This is
defined once in `plugins/trip/references/agent-routing.md` and referenced by name ("stateless")
rather than re-derived in each skill's own notes.

State is stored per-target under `.codex-bridge/` (gitignored), keyed so a plan's plan-review and
its code-review reports never collide (`<plan-path>#batch-review-2`, etc.). `reset`/`show` runtime
actions drop or display the stored state without invoking Codex.

## The roles

| Skill | Access | Completion tags |
| :--- | :--- | :--- |
| `codex-plan-review` | read-only | `APPROVED`, `REQUEST_CHANGES`, `NEEDS_REWORK` |
| `codex-code-review` | read-only | same three — plus a post-convergence `synthesize` step producing the consolidated review promoted into the release CR |
| `codex-batch-review` | read-only | `BATCH_APPROVED`, `BATCH_REQUEST_FIXES` |
| `codex-implement` | write | `IMPLEMENTATION_COMPLETE`, `IMPLEMENTATION_PARTIAL` — the one skill using `--resume-last`, since continuing the same batch *is* the point |
| `codex-fix` | write | `FIX_COMPLETE`, `FIX_PARTIAL` — applies only supplied findings, never expands scope |
| `codex-test` | write | `TESTS_GREEN`, `TESTS_RED` |
| `codex-workspace` | restricted write | `WORKSPACE_COMPLETE`, `WORKSPACE_BLOCKED` — branch/stage/commit/push only, no stash/merge/tag without explicit authorization |
| `codex-release` | restricted write | `RELEASE_COMPLETE`, `RELEASE_BLOCKED` |
| `codex-release-verify` | read-only | `RELEASE_APPROVED`, `RELEASE_REQUEST_CHANGES` |
| `codex-ask` | read-only | Advisory only, no verdict tag — a second opinion on any question, not gated on the answer |

Every role-skill except `codex-ask` is deliberately thin: the `SKILL.md` is an orchestration
skeleton around `plugins/codex-bridge/scripts/codex-run.py`, and the actual prompt content is disclosed into
`skills/<name>/prompts/*.tpl`, loaded only when that role runs.

## Why not just `/codex:review`

OpenAI's own `/codex:review` reviews a diff cold and emits a two-state verdict. `codex-code-review`
grounds the same review in this project's `docs/archi/` and `docs/3-code-review/checklist.md`,
suppresses false-positive classes TRIP cares about, and emits the three-state verdict `TRIP-2`
branches on. `/codex:adversarial-review` is still worth running *alongside* it for risky changes —
it attacks the design, which neither review does.
