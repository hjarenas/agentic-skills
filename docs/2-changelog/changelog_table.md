# Changelog Table

| Version   | Week | Commit Message                  |
| --------- | ---- | -------------------------------- |
| `0.2.0`   | 1    | feat(trip): add git-worktree-based flow and phase parallelism |
| `0.1.0`   | 1    | chore: initialize TRIP workflow |

# Changelog Summary

- **v0.2.0 (TRIP Worktree Parallelism — Week 1, 15-08-2026)**:
  - **`trip` (1.4.0 → 1.5.0)**: added git-worktree-based flow parallelism (one worktree per TRIP flow) and phase parallelism (dependency-graph-driven parallel worktree-isolated batch loops per independent plan phase), with serialized phase-merge/cleanup, explicit merge-conflict-in-place resolution, and updated failure-handling guarantees (bumps from 1.4.0, not the originally planned 1.3.0, because an unrelated PR adding named per-role subagents merged to `main` first and independently bumped `trip` to 1.4.0)
  - **`codex-bridge` (1.2.1 → 1.2.2)**: fixed `codex-code-review`'s diff baseline to `git diff $(git merge-base <main> HEAD)` so mid-flow phase commits no longer narrow the reviewed diff
  - **Code review**: Codex loop, 5 rounds -> APPROVED (`docs/3-code-review/CR_w1_v0.2.0.md`)

- **v0.1.0 (TRIP Initialization — Week 1, 11-08-2026)**:
  - **Setup**: initialized TRIP workflow with docs structure
  - **Documentation**: built the architecture wiki at `docs/archi/` (6 pages: distribution, and one per plugin — trip, trip-wiki, codex-bridge, pocock-core, toolbox)
  - **Files added**: docs/TRIP.md, docs/archi/, docs/3-code-review/{checklist,cr-template}.md, docs/4-unit-tests/TESTING.md
