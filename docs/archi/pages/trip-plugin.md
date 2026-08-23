---
title: trip plugin
status: current
updated: 2026-08-24
verified-at: 1.7.1
links: [distribution, trip-wiki-plugin, codex-bridge-plugin, worktree-parallelism]
---

The Plan → Implement → Release orchestration workflow. `trip` skills never touch code, tests, or
git themselves — they dispatch **workers** (subagents, or [[codex-bridge-plugin]] skills) and
consume typed completion tags. See [[distribution]] for how this plugin is versioned and shipped.
This separation is the **agent routing contract**
(`plugins/trip/references/agent-routing.md`), read by every phase skill before it does anything.

## The phases

| Skill | Model-invokable | Role |
| :--- | :--- | :--- |
| `TRIP-init` | No | One-time setup: `docs/TRIP.md` profile, docs structure, hands off to `wiki-init` |
| `TRIP-1-plan` | Yes | Discovery → clarification → plan doc → independent plan review → user approval |
| `TRIP-2-implement` | Yes | Batched implementation, delta review per batch, testing gate, independent code review |
| `TRIP-3-release` | Yes | Version bump, changelog, `wiki-ingest`, commit, **pull request** (not a direct merge) |
| `TRIP-auto` | No | Chains all three phases with exactly one human checkpoint (plan approval) |
| `TRIP-hotfix` | No | Emergency path; exempt from worker-dispatch, never exempt from the PR gate |
| `TRIP-research`, `TRIP-review`, `TRIP-test` | No | Standalone: spike investigation, manual review audit, deep test authoring |
| `TRIP-upgrade` | No | Migration onto the plugin model, plus standalone backfills an already-migrated project still needs |
| `TRIP-compact` | No | Legacy, superseded by `wiki-migrate` — kept as a stopgap only |

`TRIP-1/2/3` and `TRIP-auto` are model-invokable so the agent can chain phases within a session
(`TRIP-2-implement` invoking `TRIP-3-release` directly on completion); every other TRIP skill
requires explicit `/` invocation because it's either a one-time setup/migration step or an
autonomy-maximizing path that shouldn't fire on its own judgment. `TRIP-init` hands architecture
documentation off to [[trip-wiki-plugin]] rather than owning it itself.

## Who waits for whom

`TRIP-auto` is the top-level orchestrator. It invokes a phase skill as a child orchestrator, and
that child dispatches role workers. The nesting remains deliberate; the fallible boundary is the
child's report back to its parent, not the on-disk work produced below it.

```text
TRIP-auto (parent orchestrator)
        | dispatch
        v
TRIP-1/2/3 (child orchestrator) -- report to parent [FALLIBLE] --> TRIP-auto
        | dispatch
        v
trip:<role> worker -- result --> child orchestrator
        | writes
        v
worktree artifacts
```

Cross-session report delivery failed for a substantial fraction of reports in an observed run, while
the work survived in its worktree. Every orchestrator therefore follows `agent-routing.md`'s
**Waiting for a worker** section: waits are bounded and passive, a live worker is never polled or
pinged for progress, and a missing report is not evidence that work is missing. Completion is
reconstructed only from validated artifact changes and observable status; the durable artifact
takes precedence over the fallible report transport.

All 11 named agents carry `disallowedTools: ..., Agent`, so a `trip:<role>` worker structurally
cannot dispatch sub-workers. A child orchestrator is therefore not one of those named agents. It
comes from outside the plugin's declared agent set, and the plugin intentionally does not name the
mechanism that creates it.

## Worktree parallelism

`TRIP-1-plan` gives each flow its own git worktree, and `TRIP-2-implement` gives each independent
plan phase (declared via a `Depends on:` line) its own worktree branched off the feature branch,
running phase batch loops in parallel and merging them back one at a time. See
[[worktree-parallelism]] for the full mechanism, including the serialized merge slot,
conflict-in-place resolution, and the `TRIP-3-release` cleanup exception.

Two workers dispatched into the *same* worktree get nothing from it — they share one working tree
and one git index — so `agent-routing.md` adds a second, finer unit: a **lane**, one worker's
exclusive writable path set for one dispatch. The six worker agent definitions that can be
dispatched concurrently (`implementer`, `fixer`, `planner`, `test-worker`, `release-worker`,
`workspace-worker`) each point at that section rather than restating it, using the shared `lane` /
`rewrite forward` / `destructive git` vocabulary. Where no disjoint lane can be drawn, the workers
are serialized instead. The same contract denies destructive git (`git stash`, `git checkout --
<path>`, `git restore`, `git reset --hard`, `git clean`) to every role, because a TRIP working tree
often holds the only copy of the work so far. See [[worktree-parallelism]].

## Named per-role subagents, not `general-purpose`

Every worker role (`discovery`, `planner`, `plan-reviewer`, `implementer`, `batch-reviewer`,
`fixer`, `test-worker`, `code-reviewer`, `workspace-worker`, `release-worker`,
`release-verifier`) has its own subagent definition at `plugins/trip/agents/<role>.md`, addressed
as `trip:<role>`. Each is scoped via `disallowedTools` to that role's read/write boundary from the
Roles table below — read-only roles deny `Write`/`Edit`/`NotebookEdit`, all of them deny `Agent`
(spawning further sub-dispatches stays an orchestrator-only privilege) — and each mandates the
same completion tag its `codex-bridge` counterpart uses, so tag-parsing logic in the orchestrator
skills is harness-agnostic. This replaced dispatching every role as the built-in `general-purpose`
agent, which worked but flattened Claude Code's usage/analytics view into one undifferentiated
bucket. An older cached `trip` install without these files yet fails a `trip:<role>` dispatch with
an "Unknown agent" error — `agent-routing.md`'s upgrade note documents the recovery (retry that
one call with `general-purpose`, then update and reload).

## The profile: `docs/TRIP.md`

Everything project-specific — commands, version file, week anchor, agent routing table, plan
considerations, guidance sections — lives in the **consuming project's** `docs/TRIP.md`, written
once by `TRIP-init` and never touched by a plugin update. Earlier versions of `trip` baked
project specifics into the `SKILL.md` files themselves, which meant every plugin update was a
three-way reconciliation; `TRIP-upgrade` exists to migrate projects off that model.

`TRIP-upgrade` is not only a one-time migration. Its Phase 0 makes **two independent decisions**:
one *structural path* (legacy skills present, profile missing `## Agent routing`, neither, or
nothing structural left to do) and a set of *standalone migrations* that each run whenever their
own condition holds — on the legacy, routing and "no structural work" paths alike. That second
axis is what lets a project already on the plugin model receive later profile and settings
backfills (currently the worktree-bootstrap subsection and the `git worktree` permission
allowlist). Before 1.7.1 there was only the structural axis, so an already-routed project hit an
"already current" exit and could never reach those backfills.

## Release lands through a PR, not a fast-forward merge

`TRIP-3-release` commits release docs on the feature branch, pushes, and opens a pull request —
tagging happens only *after* the user merges on GitHub (`TRIP-3-release` Step 11). `TRIP-auto`'s
Phase 4 explicitly documents this as replacing an earlier push-to-main flow. (Both skills'
descriptions said "ff-merge" until 2026-08-11; fixed to say "pull request.")

Step 10 checks for a stale base with `git fetch` plus `git merge-tree` and stops on
`WOULD CONFLICT` — first in the step, before `gh pr create` runs. A flow can run for hours while
other work merges, and the first anyone learns of a stale base is usually a conflicted pull request
the user has to point out; the check moves that discovery ahead of opening the PR. A conflict is
handed back to an `implementer` lane plus a re-run of the testing gate rather than a quick rebase,
because the resolution rewrites reviewed, gate-verified content. The artifact-writing steps themselves fan out across three lane-scoped
`release-worker` dispatches, with one `release-verifier` over the combined diff — see
[[worktree-parallelism]].

## Codex is stateless

Every `codex-bridge` worker `trip` dispatches is a fresh process with no memory between turns —
continuity travels only through `--notes`. This is defined once in `agent-routing.md`'s
Codex-bridge section rather than re-derived in each phase skill. See [[codex-bridge-plugin]].
