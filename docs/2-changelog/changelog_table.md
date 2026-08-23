# Changelog Table

| Version   | Week | Commit Message                  |
| --------- | ---- | -------------------------------- |
| `1.7.0`   | 2    | feat(trip): add worker lanes, worktree bootstrap and release fan-out |
| `1.6.0`   | 2    | feat(trip): add orchestrator bounded-wait and lost-report recovery contract |
| `0.2.0`   | 1    | feat(trip): add git-worktree-based flow and phase parallelism |
| `0.1.0`   | 1    | chore: initialize TRIP workflow |

# Changelog Summary

- **v1.7.0 (Worker Lanes, Worktree Bootstrap and Release Fan-Out — Week 2, 23-08-2026)**:
  - **`trip` (1.6.0 → 1.7.0)**: closed five framework gaps found by mining 37 downstream Claude Code transcripts for tool-result error traces rather than user corrections — each gap had been worked around by hand in per-dispatch prompts
  - **Lanes** (`references/agent-routing.md`): a lane is one worker's exclusive writable path set for one dispatch — worktrees isolate a *phase*, lanes isolate a *worker inside* a worktree, since two workers in one worktree share a working tree and git index; evidence was 86 hand-written "another agent is editing X" warnings, and lanes prevent a tree-wide formatter rewriting a sibling's mid-edit files, `git add -A` sweeping half-finished work, and two workers overwriting one file. The git index sits outside every lane (it belongs to `workspace-worker`, dispatched alone); no lane ⇒ no concurrency, serialize instead
  - **Destructive git banned for every role**: `git stash`, `git checkout -- <path>`, `git restore`, `git reset --hard`, `git clean` — TRIP projects may defer committing until release, so the working tree routinely holds the only copy of all batches so far (this destroyed uncommitted work twice downstream); the positive target is **rewrite forward**
  - **Worktree bootstrap** (`TRIP-init` profile subsection, wired into `TRIP-2-implement` and `phase-scheduling.md`, migrated by `TRIP-upgrade`): worktrees carry only tracked files, so absent `.env` and `node_modules` made a gate fail like a real regression; the profile now also records what is shared per-machine rather than per-worktree (Docker, fixed ports)
  - **Git permission allowlist** (`TRIP-init` Phase 5b, migrated by `TRIP-upgrade`): `git worktree` was never pre-approved, so autonomous runs stalled on prompts and parallel phases serialized behind them; destructive git and `git push --force` are deliberately excluded so they keep prompting
  - **Release fan-out and stale-base check** (`TRIP-3-release`): Steps 1-8 were one serial dispatch though most write disjoint files — Step 1 now runs alone, then three parallel lane-scoped `release-worker` dispatches (version+README / code-review+changelog / `wiki-ingest`, the long pole), then Step 4, with one verifier over the combined diff; Step 10 runs `git fetch` + `git merge-tree` before pushing, ahead of `gh pr create` in the same step, and blocks on `WOULD CONFLICT` — a flow can run for hours while other work merges, and the first anyone learns of a stale base is usually a conflicted PR the user has to point out, so the check moves that discovery before the PR exists; a conflict routes back through an `implementer` lane plus a re-run of the testing gate rather than a quick rebase, since resolving it rewrites reviewed, gate-verified content
  - **Six agent definitions** (`implementer`, `fixer`, `planner`, `test-worker`, `release-worker`, `workspace-worker`) each carry a short pointer using the `lane` / `rewrite forward` / `destructive git` tokens back to the contract, rather than a duplicated paragraph
  - **Code review**: Codex skipped (unplanned change from transcript analysis), manual CR -> APPROVED with observations (`docs/3-code-review/CR_w2_v1.7.0.md`)

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
