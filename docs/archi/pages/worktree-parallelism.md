---
title: Worktree parallelism
status: current
updated: 2026-08-20
verified-at: 1.6.0
links: [trip-plugin, codex-bridge-plugin]
---

TRIP flows and their implementation phases run in dedicated git worktrees rather than in the
primary working tree, so concurrent flows and concurrent phases within one flow never share a
mutable working directory. Introduced in [[trip-plugin]] 1.5.0
(`docs/1-plans/F_0.2.0_trip-worktree-parallelism.plan.md`; bumps from 1.4.0, not the originally
planned 1.3.0, because an unrelated named-per-role-subagents change merged first).

## Outer parallelism — one worktree per flow

`TRIP-1-plan`'s persist step (`plugins/trip/skills/TRIP-1-plan/SKILL.md`, "Persist and confirm")
creates `../<repo>-<slug>-<suffix>` via `git worktree add ... -b feat/<slug>-<suffix> <main
branch>` instead of checking out a branch in the primary tree, commits the approved plan file
there, and pushes. Every worker dispatched for the rest of that flow — `TRIP-2-implement`,
`TRIP-3-release`, and their own workers — carries that worktree path explicitly as its working
directory; nothing relies on the caller's current directory. Two flows started concurrently never
touch the same tree.

A resumed flow locates its worktree by matching the commit that added the plan file against `git
worktree list`, then filtering out any candidate whose branch name matches the phase-branch suffix
pattern (`-phase-[0-9]+$`) — phase branches also contain that commit, since they branch off the
feature branch, so without the filter a resumed lookup during an open frontier is ambiguous
(`plugins/trip/skills/TRIP-2-implement/SKILL.md`, "Step 0"). Exactly one candidate must remain.

## Inner parallelism — one worktree per independent phase

A plan's `### Phase N` headings each carry a `Depends on:` line
(`plugins/trip/skills/TRIP-1-plan/SKILL.md`, plan-body template). `TRIP-2-implement` computes the
**frontier** — every unmerged phase whose dependencies are all merged — and dispatches one
worktree-isolated batch loop per frontier phase in parallel, each in
`../<repo>-<slug>-<suffix>-phase-<n>` on branch `feat/<slug>-<suffix>-phase-<n>`, branched off the
feature branch (`plugins/trip/skills/TRIP-2-implement/SKILL.md`, "Phase Scheduling"). The branch
name is deliberately flat and hyphen-joined (`feat/<slug>-<suffix>-phase-<n>`, never nested as
`feat/<slug>-<suffix>/phase-<n>`) because git stores branch refs as a path hierarchy under
`.git/refs/heads/`: once `feat/<slug>-<suffix>` exists as a ref (a file), a name nested under it
is invalid.

`TRIP-1-plan`'s plan review validates the dependency graph before presentation: at least one phase
must say `Depends on: none`, and the graph must have no cycles, or `TRIP-2-implement` could be
left with unmerged phases and an empty frontier.

## Phase gate and serialized merge

Each phase's batch loop runs its own delta review and scoped testing gate exactly as a
single-phase flow would. Once a phase clears that gate, `workspace-worker` commits on the phase
branch, merges it into the feature branch with `git merge --no-ff`, pushes the feature branch,
removes the phase worktree, and deletes the phase branch
(`plugins/trip/skills/TRIP-2-implement/SKILL.md`, "Phase gate and merge").

This merge/cleanup step is **serialized** across phases even though implementation and gating stay
parallel: a single working tree and `.git` is not safe for concurrent mutating git operations. A
phase holds an exclusive merge slot against the feature worktree from the start of its merge step
until its own `WORKSPACE_COMPLETE` — a `WORKSPACE_BLOCKED` result retains the slot rather than
releasing it, and an unresolved merge conflict is a terminal stop that blocks any further merge
dispatch. A conflicted merge is resolved **in place** — files fixed, staged, and committed to
complete the existing merge — never aborted and retried, since retrying an unchanged merge against
unchanged branches reproduces the same conflict.

If the slot holder dies or its report is lost, every other phase is stranded at the merge slot,
even when its isolated implementation and gate have finished. Recovery follows
`plugins/trip/skills/TRIP-2-implement/phase-scheduling.md`'s **Phase gate and merge** section: dispatch a read-only `workspace-worker`
audit and require its four-part observable merge test. Only the observed **merge landed; slot
releasable** condition releases the slot; any failed or ambiguous observation keeps it held and
stops the scheduling loop.

After every phase has merged, the feature-wide Testing Gate and the single independent code review
run exactly once over the integrated feature — per-phase gates are delta review plus scoped
testing; the feature-wide deep review is the only pass positioned to catch cross-phase integration
issues.

## Failure handling

`TRIP-auto`'s stop-state guarantee ("the feature branch is always left in a clean, pushed state
when stopping mid-way") is exempted for exactly one case: an unresolved merge conflict during
phase scheduling deliberately leaves the feature worktree mid-merge — conflict markers present,
that phase's work not yet committed or pushed — so a human can resolve or abort it
(`plugins/trip/skills/TRIP-auto/SKILL.md`, "Failure handling"). Every other stop condition still
leaves the feature branch clean and pushed. Worktrees are left in place rather than removed on any
stop, so a resumed session or a human can inspect or continue from exactly where the run stopped.

A dead or silent merge-slot holder has the same flow-wide blast radius: every other phase is
stranded behind it. The recovery path is the read-only `workspace-worker` audit plus the four-part
observable merge test in `phase-scheduling.md`'s **Phase gate and merge** section. A conclusive
test can release the slot and leave cleanup to a separate worker; an inconclusive test leaves the
slot held and the worktrees intact for inspection rather than allowing another merge on a guess.

## Release cleanup — the one cwd exception

`TRIP-3-release` runs inside the feature worktree for steps 1-10, but git cannot remove the
worktree that is the current working directory. Its final cleanup step is the one point in the
whole flow that deliberately switches back to the primary working tree, updates the main branch
there, removes the feature worktree (`git worktree remove ../<repo>-<slug>-<suffix>`), and only
then deletes the now-unused feature branch (`plugins/trip/skills/TRIP-3-release/SKILL.md`, final
steps).

## Codex-side implications

- `codex-workspace`'s allowlist gained `git worktree add`, `git worktree remove`, and `git merge
  --no-ff` as an allowlistable operation class for flow/phase lifecycles — denied by default,
  permitted only when a dispatch's `--extra` explicitly lists each authorized operation
  (`plugins/codex-bridge/skills/codex-workspace/SKILL.md`). See [[codex-bridge-plugin]].
- `codex-code-review`'s diff baseline changed from `git diff HEAD` to `git diff $(git merge-base
  <main branch> HEAD)`, fixed in `codex-bridge` 1.2.2 because once phases commit mid-flow, `git
  diff HEAD` would silently narrow to only the most recent phase's commit instead of the whole
  feature (`plugins/codex-bridge/skills/codex-code-review/prompts/start.tpl`, `resume.tpl`).
- Concurrent phases in separate worktrees can safely use `--resume-last`: the installed `codex`
  companion hashes each workspace's canonical `git rev-parse --show-toplevel` path for its
  job-storage directory, isolating thread tracking per worktree. This depends on the current,
  unpinned companion version and should be regression-checked after companion upgrades
  (`plugins/codex-bridge/skills/codex-implement/SKILL.md`).
