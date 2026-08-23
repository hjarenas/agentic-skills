---
title: Worktree parallelism
status: current
updated: 2026-08-23
verified-at: 1.7.0
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

## Lanes — isolation inside a worktree

A worktree isolates a **phase**; it grants nothing to two workers dispatched into the *same*
worktree, because they share one working tree and one git index. The unit that isolates those
workers is the **lane**: one worker's exclusive writable path set for one dispatch, defined in
`plugins/trip/references/agent-routing.md`'s **Lanes** section (added in `trip` 1.7.0). Lanes are
the second, finer isolation scale beneath the worktree, and every parallel dispatch into a shared
worktree carries one.

Three failure modes motivated it, all observed downstream and all silent — nothing errors, the
work is simply wrong afterwards: a tree-wide formatter rewriting a sibling's mid-edit files, a
`git add -A` sweeping a sibling's half-finished work into a commit, and two workers writing the
same file. Before lanes existed the contract was written by hand, per dispatch, as "another agent
is concurrently editing X — do not touch" — 86 such warnings across the mined transcripts.

Two rules close the mechanism:

- **The git index sits outside every lane.** It belongs to `workspace-worker`, which is always
  dispatched alone — which is why the serialized merge slot below is a separate mechanism rather
  than just another lane.
- **No lane ⇒ no concurrency.** A set of workers whose writable paths cannot be made disjoint is
  serialized instead of parallelized.

## Destructive git is banned in every worktree

`git stash`, `git checkout -- <path>`, `git restore`, `git reset --hard` and `git clean` are
denied to every role (`plugins/trip/references/agent-routing.md`, **Destructive git**). The reason
is specific to this flow shape: a TRIP project may defer committing until release, so a phase
worktree's working tree routinely holds the **only** copy of every batch completed so far, and
these commands are exactly the ones that discard it. The positive replacement is to **rewrite
forward** — undo an edit by writing the intended content again. The `TRIP-init` git allowlist
(below) deliberately excludes these commands and `git push --force` so they keep prompting.

## Bootstrapping a fresh worktree

A worktree checkout carries only **tracked** files, so gitignored configuration (`.env`) and
installed dependencies (`node_modules`) are absent in every newly created flow or phase worktree,
and the gate that then fails is indistinguishable from a real regression. `TRIP-init` therefore
records a per-project **"Bootstrapping a fresh worktree"** subsection in `docs/TRIP.md`
(`plugins/trip/skills/TRIP-init/SKILL.md`), read by `plugins/trip/skills/TRIP-2-implement/SKILL.md`
and its `phase-scheduling.md` whenever a worktree is created; `TRIP-upgrade` migrates existing
profiles. The same subsection records what is shared **per machine** rather than per worktree —
Docker daemons, fixed host ports — which is the constraint that decides whether two phase
worktrees can actually run their gates at once.

`TRIP-init` Phase 5b additionally writes a git permission allowlist covering `git worktree`, which
was never pre-approved: autonomous runs stalled on permission prompts and parallel phases
serialized behind the approvals rather than behind any real dependency.

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

## Release fan-out

`TRIP-3-release` Steps 1-8 ran as one serial dispatch even though most of those steps write
disjoint files. Since `trip` 1.7.0 (`plugins/trip/skills/TRIP-3-release/SKILL.md`) Step 1 runs
alone, then **three lane-scoped `release-worker` dispatches run in parallel** in the one feature
worktree — version + README, code review + changelog, and `wiki-ingest` (the long pole) — followed
by Step 4. The lanes are what makes sharing the worktree safe; see **Lanes** above. Verification
does not fan out with the writing: a single `release-verifier` still reviews the combined diff.

Step 10 runs `git fetch` plus `git merge-tree` against the main branch before pushing and stops on
`WOULD CONFLICT` rather than rebasing. The check runs first in that step, ahead of `gh pr create`:
a flow can run for hours while other work merges, and the first anyone learns of a stale base is
usually a conflicted pull request the user has to point out, so the check moves that discovery
earlier — before the PR is opened. A conflict routes back through an `implementer` lane and a
re-run of the testing gate rather than a quick rebase, because resolving it rewrites reviewed,
gate-verified content and so earns review and a gate of its own.

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
