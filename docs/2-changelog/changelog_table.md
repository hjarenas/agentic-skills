# Changelog Table

| Version   | Week | Commit Message                  |
| --------- | ---- | -------------------------------- |
| `1.6.0`   | 2    | feat(trip): add orchestrator bounded-wait and lost-report recovery contract |
| `0.2.0`   | 1    | feat(trip): add git-worktree-based flow and phase parallelism |
| `0.1.0`   | 1    | chore: initialize TRIP workflow |

# Changelog Summary

- **v1.6.0 (Orchestrator Bounded Wait — Week 2, 20-08-2026)**:
  - **`trip` (1.5.0 → 1.6.0)**: replaced an unbounded busy-wait with a bounded wait contract in `references/agent-routing.md`, reached by every orchestrator skill and agent
  - **Evidence over inference**: dispatch-time baseline plus a validated delta decides completion at the cap, instead of inferring it from a missing message
  - **Lost-report recovery**: the dispatcher resumes a stopped child from its transcript rather than re-dispatching, and an orphaned report surfacing in the wrong conversation must be relayed to the blocked parent — lost reports proved common (~1 in 3), so these are normal paths, not emergency ones
  - **Merge-slot recovery**: the stuck serialized merge slot can be released, but only on four observations by a read-only audit worker — (1) no git operation in progress (`MERGE_HEAD`, both rebase-state forms, `CHERRY_PICK_HEAD` absent) and a clean worktree, (2) feature `HEAD` is a merge commit, (3) that phase's recorded expected tip is one of `HEAD`'s parents, (4) the `git ls-remote` feature ref equals that exact `HEAD`; checks 2-4 are the identity half, so another phase's merge can never release a slot it does not own, and any failure or ambiguity stops the loop with the slot still held
  - **Completion tags** added for `discovery` and `planner`, framed as report integrity rather than liveness
  - **Contradictions resolved**: release nesting (nested under `TRIP-auto`, flat standalone) and `TRIP-auto`'s user-interaction count (surviving prompts suppressed; the failure stop named as a third, exceptional interaction)
  - **Code review**: Codex loop, 2 rounds -> APPROVED (`docs/3-code-review/CR_w2_v1.6.0.md`)

- **v0.2.0 (TRIP Worktree Parallelism — Week 1, 15-08-2026)**:
  - **`trip` (1.4.0 → 1.5.0)**: added git-worktree-based flow parallelism (one worktree per TRIP flow) and phase parallelism (dependency-graph-driven parallel worktree-isolated batch loops per independent plan phase), with serialized phase-merge/cleanup, explicit merge-conflict-in-place resolution, and updated failure-handling guarantees (bumps from 1.4.0, not the originally planned 1.3.0, because an unrelated PR adding named per-role subagents merged to `main` first and independently bumped `trip` to 1.4.0)
  - **`codex-bridge` (1.2.1 → 1.2.2)**: fixed `codex-code-review`'s diff baseline to `git diff $(git merge-base <main> HEAD)` so mid-flow phase commits no longer narrow the reviewed diff
  - **Code review**: Codex loop, 5 rounds -> APPROVED (`docs/3-code-review/CR_w1_v0.2.0.md`)

- **v0.1.0 (TRIP Initialization — Week 1, 11-08-2026)**:
  - **Setup**: initialized TRIP workflow with docs structure
  - **Documentation**: built the architecture wiki at `docs/archi/` (6 pages: distribution, and one per plugin — trip, trip-wiki, codex-bridge, pocock-core, toolbox)
  - **Files added**: docs/TRIP.md, docs/archi/, docs/3-code-review/{checklist,cr-template}.md, docs/4-unit-tests/TESTING.md
