Full mechanism for scheduling and merging independent plan phases in parallel, referenced from
`SKILL.md`'s "Phase Scheduling" step. Three rules here must not be relaxed: the merge slot stays
held through the whole conflict-resolution sub-flow, not just until `WORKSPACE_BLOCKED`; and
`WORKSPACE_COMPLETE` only fires after commit, push, and cleanup all finish; and a silent
merge/cleanup worker releases its stuck merge slot only after the phase-specific recovery audit
below observes that phase's merge landed and was pushed.

## Frontier computation

Parse the `Depends on:` line under every phase heading and track which phases have merged into
the feature branch. Compute the current **frontier** as every unmerged phase whose dependencies
are all merged; initially this is every `Depends on: none` phase. If the frontier is empty while
any unmerged phase remains, on the first or any later round, stop immediately and report that the
plan's dependency graph has no root or contains a cycle. Do not retry, idle, or limit this check to
the case where no phase has merged yet.

For every phase in the frontier, dispatch `workspace-worker` in parallel to create a phase branch
and worktree from the feature branch, reusing the outer flow's collision-safe suffix:

```bash
git worktree add ../<repo>-<slug>-<suffix>-phase-<n> \
  -b feat/<slug>-<suffix>-phase-<n> feat/<slug>-<suffix>
```

Use the corresponding `fix/` prefix when the flow branch uses it. The phase branch name must be
flat and hyphen-joined; never use `feat/<slug>-<suffix>/phase-<n>`, because the existing feature
ref is a file in git's ref hierarchy and cannot also be a parent directory. Creating a differently
named branch from a branch checked out in another worktree is valid.

Run one instance of the batch loop (`SKILL.md`'s "Per-Phase Implementation") inside each phase
worktree, scoped only to that phase's checkboxes, with one loop dispatched per frontier phase in
parallel. Carry each phase worktree's path explicitly as the working directory for all of its
workers. Sibling phase slots proceed independently.

## Phase gate and merge

After all batches for a phase are staged, run its gate before merging:

1. Dispatch `batch-reviewer` for the **full phase diff** and phase blast radius, not only the last
   batch. Route corrections to `fixer` and re-review until clean.
2. Dispatch `test-worker` for the lint, typecheck/build, and affected tests from the Testing Gate
   below, explicitly scoped to that phase's files. Route failures to `fixer` and re-run the phase
   gate.
3. On pass, the phase is **merge-ready**. Dispatch `workspace-worker` to commit on the phase
   branch; record that phase branch's expected tip before dispatch. Merge it into the feature
   branch with `git merge --no-ff`, push the feature branch, remove the phase worktree, and delete
   the phase branch. Before deleting, require `git merge-base --is-ancestor <phase-tip>
   <feature-branch>` to succeed; do not rely on `git branch -d` comparing the phase branch with
   whichever unrelated branch the primary repository currently has checked out. Once that check
   succeeds, delete with `git branch -D`: the ancestry check, not `-d`'s HEAD-relative check, is
   the authority. This per-phase merge commit replaces the single implementation commit formerly
   deferred to `TRIP-3-release`; that skill's final release-documentation commit remains unchanged.
   Pushing here keeps the remote feature branch in sync with each local phase merge as it lands,
   the same way `TRIP-1-plan` pushes eagerly at persist time.

**Merge/cleanup is serialized.** Implementation and gating (steps 1-2 above) stay parallel across
phases — each phase runs in its own isolated worktree with no shared mutable state. But step 3
mutates the shared feature-branch worktree, and a single working tree/`.git` is not safe for
concurrent mutating git operations. If multiple phases become merge-ready around the same time,
dispatch step 3 for one phase at a time, and hold that phase's merge slot — no other phase's merge
may be dispatched against the feature worktree — from the moment its merge/cleanup step begins
until that *same* phase's merge is fully resolved and the feature worktree is back to a clean,
non-mid-merge state. A `WORKSPACE_BLOCKED` report does **not** release the slot: it surfaces a
merge conflict while deliberately leaving the feature worktree mid-merge (conflict markers
present, merge in progress) so it can be resolved in place — see "Merge conflict handling" below.
A stuck slot strands every other phase: none can merge even when its isolated implementation and
gate have finished. Sibling phases still implementing or gating are unaffected and continue in
parallel until they need the slot.

On the normal report path, that same phase's `WORKSPACE_COMPLETE` proves both that its merge
landed and that cleanup finished, so release the slot.

If that phase's merge/cleanup worker stays silent through the bounded wait in `agent-routing.md`'s
**Waiting for a worker**, keep the slot held and dispatch a **new, read-only `workspace-worker`
audit**. The orchestrator runs no git itself, as required by `agent-routing.md`'s **Orchestrator
boundary**. Give the auditor the recorded expected tip of that specific phase branch and require
all four observations:

1. No in-progress git operation in the feature worktree (`MERGE_HEAD`, `rebase-merge/`,
   `rebase-apply/`, `CHERRY_PICK_HEAD` all absent) and the worktree is clean.
2. Feature `HEAD` is a merge commit (two parents), not a fast-forward or some later unrelated
   commit.
3. The recorded expected tip of that specific phase branch is one of `HEAD`'s parents.
4. The remote feature ref observed with `git ls-remote` equals that exact `HEAD`.

Dispatch a different worker to report repository state. A clean tree and some pushed commit are
insufficient; they could belong to the wrong phase. Only all four observations establish **merge
landed; slot releasable**. This narrow state is distinct from `WORKSPACE_COMPLETE`, which also
requires phase worktree and branch cleanup. Record the reconstructed merge and its four observations in the flow
notes, release the merge slot, and allow the next ready phase to merge.

After releasing the slot, dispatch a separate `workspace-worker` assignment scoped to cleanup only:
remove that phase worktree and delete that phase branch, nothing else. Require it to verify `git
merge-base --is-ancestor <phase-tip> <feature-branch>` before deletion, then delete with `git
branch -D` — the ancestry check, not `-d`'s HEAD-relative check, is the authority. Do not hold the
merge slot for this cleanup, but do not count the phase as fully `WORKSPACE_COMPLETE` until it
succeeds.

If any audit check fails or any result is ambiguous, stop the whole phase-scheduling loop and
surface the observations. Keep the slot held. Releasing on inferred rather than observed state is
the one failure here that can corrupt the feature branch.

**Merge conflict handling.** `git merge --no-ff` leaves a conflict in progress — conflict markers
in the files, unmerged entries in the index — unless explicitly aborted, so on conflict
`workspace-worker` must **not** run `git merge --abort`. It reports `WORKSPACE_BLOCKED` with the
conflicting file list while the merge stays in progress; this is an intermediate status within that
phase's still-open merge attempt, not a terminal outcome, and the phase's merge slot from above
stays held throughout. Route an `implementer` scoped only to the conflicting files to resolve them
directly in the feature-branch worktree, which is mid-merge: the implementer edits the
conflict-marked files to their correctly resolved content and removes the conflict markers (the
phase worktree is discarded regardless). Re-run the normal phase gate over that resolution —
`batch-reviewer` reviews the merge's resulting diff, plus scoped testing. On approval,
`workspace-worker` runs `git add <resolved files>` then `git commit` — this finishes the
in-progress merge commit directly. There is no "retry the merge" step: committing a resolved merge
*is* completing it, and a fresh `git merge --no-ff` invocation would only hit the same conflict
again, since nothing about either branch's history changed. `workspace-worker` then pushes the
feature branch, removes the phase worktree, and deletes the phase branch, as in the normal case —
verify `git merge-base --is-ancestor <phase-tip> <feature-branch>` before deletion, then delete
with `git branch -D`, the ancestry check being the authority rather than `-d`'s HEAD-relative
check. Only after all of that, with the feature worktree fully clean, does it report that same
phase's `WORKSPACE_COMPLETE` and release the merge slot. Only that phase's slot pauses while
sibling phases continue implementing or gating. If conflicts recur on re-review, surface
`WORKSPACE_BLOCKED` to the user instead of retrying indefinitely — and because the merge slot is
still held with the feature worktree stuck mid-merge, this stops the entire phase-scheduling loop,
not just that one phase: no other phase's merge/cleanup may be dispatched against the same feature
worktree until a human resolves it. Record in the flow's running notes, for the PR description and
future planners, that this phase pair's dependency judgment was wrong; do not retroactively edit
this plan's dependency graph.

After each successful merge, recompute the frontier so newly unblocked phases enter the next
round. Repeat until every phase has merged.
