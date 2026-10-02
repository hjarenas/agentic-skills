# Code Review: Waiting by Inactivity, Worker Dispatch Discipline, Origin as Release Ground Truth

**Review Date**: 2026-10-02
**Version**: 1.8.0
**Files Reviewed**: the full change set is 25 paths, derived from `git diff --name-only
origin/main...HEAD` plus `git status --short`. The independent `code-reviewer` examined:
- the 18 feature paths, marked * below, in all three rounds;
- the 3 wiki paths, marked †, in round 3.

The remaining 4 release artifacts are covered by `release-verifier`. The 11 agent definitions under
`plugins/trip/agents/` were reviewed in rounds 2 and 3 as a patch, listed at the end. The patch was
applied unchanged as its own commit in this release (see Verdict).

- `README.md` *
- `plugins/codex-bridge/.claude-plugin/plugin.json` *
- `plugins/codex-bridge/skills/codex-code-review/SKILL.md` *
- `plugins/codex-bridge/skills/codex-implement/SKILL.md` *
- `plugins/codex-bridge/skills/codex-release/SKILL.md` *
- `plugins/codex-bridge/skills/codex-release/prompts/release.tpl` *
- `plugins/trip/.claude-plugin/plugin.json` *
- `plugins/trip/references/agent-routing.md` *
- `plugins/trip/skills/TRIP-1-plan/SKILL.md` *
- `plugins/trip/skills/TRIP-2-implement/SKILL.md` *
- `plugins/trip/skills/TRIP-2-implement/phase-scheduling.md` *
- `plugins/trip/skills/TRIP-3-release/SKILL.md` *
- `plugins/trip/skills/TRIP-auto/SKILL.md` *
- `plugins/trip/skills/TRIP-hotfix/SKILL.md` *
- `plugins/trip/skills/TRIP-init/SKILL.md` *
- `plugins/trip/skills/TRIP-review/SKILL.md` *
- `plugins/trip/skills/TRIP-test/SKILL.md` *
- `plugins/trip/templates/cr-template.md` *
- `docs/archi/pages/trip-plugin.md` †
- `docs/archi/pages/worktree-parallelism.md` †
- `docs/archi/log/v1.8.0.md` †
- `docs/TRIP.md`
- `docs/2-changelog/w8_v1.8.0.md`
- `docs/2-changelog/changelog_table.md`
- `docs/3-code-review/CR_w8_v1.8.0.md`
- Patch (rounds 2-3): `plugins/trip/agents/{batch-reviewer,code-reviewer,discovery,fixer,implementer,planner,plan-reviewer,release-verifier,release-worker,test-worker,workspace-worker}.md`

**Plan**: no plan document. The change was derived from an analysis of 32 downstream `crm`
sessions and 1,728 worker transcripts; that analysis was published separately and served as the
requirements.

---

## Executive Summary

A month of `crm` runs showed the TRIP review gates earning their cost, while time and tokens leaked
between them:
- background workers hung for 10-16 hours on permission prompts the user could not see;
- a flat 20-minute wait cap fired on healthy 40-minute workers;
- one orchestrator spent 2.9 B input tokens on 1,613 no-op polls;
- full-length worker reports drove compactions;
- workers ran in the wrong checkout;
- `git add -A` swept unrelated files into commits;
- a literal `wa_` placeholder shipped in released file names;
- release figures came from stale local `main`;
- redundant confirmations stalled unattended runs for hours.

This release moves those lessons into the routing contract and the phase skills. It was reviewed
by an independent `code-reviewer` over three rounds: 1 Critical, 10 Major (counting the round-1
agent-file findings that the patch fixes), 18 Minor and 3 Suggestions, all addressed. The review's
most valuable catch was a regression the change itself introduced (see Findings). **APPROVED**,
conditional on the agent patch shipping in the same PR. That condition is met: the patch landed
unchanged.

---

## Changes Overview

All changes are prose. No scripts change, so `codex-bridge`'s unit tests (7, passing) are
unaffected.

- **`agent-routing.md`**
  - Waiting: a stall is now detected by worker inactivity (about 15 minutes with no transcript or
    output activity) rather than elapsed time. There is one watchdog per flow, no-op polling is
    banned, and an orchestrator may not end a turn idle. The activity sources are named per
    harness.
  - Dispatch contract: a literal location check (exempting worktree creation), a report of about
    25 lines, foreground-only commands, `BLOCKED` on a denied tool, and no `TRIP-*` skill inside a
    worker.
  - New subsections: "Clean-tree check" and "Model and effort on the subagent harness", which adds
    a `subagent:<agent-name>` harness value for pinned agents.
  - New "Talking to the user" section.
  - The release commit moves to `workspace-worker`, and the upgrade note is trimmed.
- **`TRIP-2-implement`**
  - Wiki and graph reads move into workers.
  - Batches are staged by explicit path, with the staged list checked against the phase-wide set.
  - Checkboxes are ticked once per phase gate.
  - A new integration-fix commit after the code-review loop.
  - No leftovers finished by the orchestrator; harness-neutral wording.
- **`phase-scheduling.md`**: the phase gate gains a tick step and stages the plan file plus
  gate-fix paths under the pre-commit clean-tree check.
- **`TRIP-3-release`**
  - `origin` is the ground truth, fetched once in Step 1, and every figure cites its command.
  - The commit goes through `workspace-worker` by path, followed by a post-commit clean-tree check.
  - The pre-PR question is dropped, the placeholder check is scoped to release files, and the PR
    template is linked rather than restated.
- **Other skills**
  - `TRIP-1-plan`: plan review runs without asking, and the template path is passed to the planner.
  - `TRIP-hotfix`: no urgency re-confirmation; feature requests are redirected.
  - `TRIP-auto`: no self-set checkpoints, status replies are status only, and the PR template
    gains a Scope section.
  - `TRIP-init`: model-tier guidance for git and release roles, and `.codex-bridge/` gitignored.
  - Template rename `wa_vx.y.z` → `w<WEEK>_v<X.Y.Z>` across `trip` and `codex-bridge`.
- **`codex-bridge`**: `codex-implement` re-dispatches leftovers and ends the turn on long
  batches, and `codex-release` no longer owns the commit.
- **README**: the release diagram and walkthrough match the new commit ownership.
- **Versions**: `trip` 1.7.1 → 1.8.0 (minor: new harness value, new sections and steps).
  `codex-bridge` 1.2.2 → 1.2.3 (patch: wording and placeholder fixes).

---

## Findings

### Critical Issues

- **Fixes made after the last phase merge would never be committed.** The first draft replaced
  TRIP-3's `git add -A` with path-based staging of release artifacts. But the testing-gate and
  code-review fixes land in the feature worktree after every phase has merged, and nothing else
  committed them, so the PR could ship without the fixes the review approved.
  **Disposition: addressed**:
  - a new TRIP-2 "Commit the integration fixes" step, repeated on the remaining-items path;
  - a post-commit clean-tree check in TRIP-3 Step 9;
  - TRIP-auto reworded.

### Major Issues

- **Phase-gate tick never staged** (`phase-scheduling.md`). **Addressed**: step 4 stages the plan
  file and the gate-fix paths.
- **Staged-list check would fail from the second batch on**, because earlier batches stay staged.
  **Addressed**: the check compares against the phase-wide union.
- **Implementer still told to tick checkboxes** (`agents/implementer.md`). **Addressed in the
  agent patch.**
- **Two owners of the release commit**: release-worker's agent file, the Roles table, the
  `codex-release` description and prompt, and the README. **Addressed**: the skill side in this
  commit set, the agent file in the patch.
- **Agent files told workers to follow `TRIP-*` skills** (planner, release-worker), contradicting
  the new ban. **Addressed in the patch**: the planner now gets the template path, which TRIP-1
  passes.
- **`codex-implement` still let the orchestrator finish leftovers.** **Addressed.**
- **README described the old release flow.** **Addressed.**
- **The clean-tree check, as first written, could never pass**: `status --porcelain` after staging
  lists the staged files. **Addressed**: one defined check with pre- and post-commit forms.
- **`.codex-bridge/` would trip every clean-tree check** on projects routing to `codex-bridge`.
  **Addressed**: a pathspec exclusion, verified by the reviewer in a scratch repository on git
  2.43, and `TRIP-init` gitignores it.
- **The patch reintroduced parallel fetches** in release-worker. **Addressed**: release-worker uses
  Step 1's fetch.

### Minor Issues

All addressed:
- model guidance moved out of the profile template block;
- worktree creation exempted from the location check;
- a single fetch in release Step 1;
- the placeholder check scoped to release files, in the skill and in the patch;
- "treat as stateless" wording;
- architecture reads in every phase's first dispatch;
- the PR template linked rather than restated;
- hotfix redirects feature requests and names its route consistently;
- release-worker description, fixer report and workspace-worker report aligned with the
  report cap;
- blank-row model guidance accurate with or without agent defaults;
- a phantom "final ticks" phrase removed;
- the handoff tick moved before the integration commit;
- the planner given the template path;
- two wiki sentences re-synced.

### Suggestions

All addressed:
- activity-timestamp locations are named per harness;
- `codex-implement` long batches end the turn rather than polling;
- the integration commit repeats on the remaining-items path.

Note (not a finding): the reviewer could not confirm that `ScheduleWakeup`/`CronCreate` exist as
tool names in a subagent. Listing them in `disallowedTools` is harmless if they don't.

---

## Checklist

- [x] 1. Functional Requirements: passed. Each rule traces to a measured incident in the `crm`
  analysis.
- [x] 2. Skill / Prompt Quality: passed. Every new prohibition is paired with its positive target
  (end the turn; stage by path; re-dispatch; measure against `origin`).
- [x] 3. Architectural Compliance: passed. The orchestrator boundary is now consistent across
  TRIP-2, TRIP-3, `codex-implement` and the agent patch.
- [x] 4. Distribution & Versioning: passed. `trip` 1.8.0 (minor) and `codex-bridge` 1.2.3 (patch);
  no skill or agent was added or removed, so the README plugin table is unchanged.
- [x] 5. Script Correctness: not applicable; no script changed.
- [x] 6. Cross-Reference Integrity: passed. The renumbered phase-gate steps resolve, no reference
  to the removed wait cap or the removed questions remains, the `plan-template.md` path resolves,
  and `wiki_lint.py` is clean over `docs/archi/`.

---

## Verdict

**APPROVED** (the condition on the agent patch is met; the patch landed unchanged in this release).

Independent `code-reviewer`, three rounds:
- round 1: REQUEST_CHANGES (1 Critical, 7 Major, 8 Minor, 1 Suggestion);
- round 2: REQUEST_CHANGES (3 Major, 7 Minor, 2 Suggestions);
- round 3: APPROVED (3 Minor, since fixed).

The approval was conditional. Round-1 findings on `implementer.md`, `release-worker.md` and
`planner.md` are fixed only by the agent-definition patch. The release session's automated
permission check blocked direct edits to agent definitions as self-modification, so the reviewed
patch was applied unchanged at the user's explicit request, as a separate commit. Without it those
three findings would have remained Major: the agents would have contradicted the skills on
checkbox ownership, commit ownership, and loading `TRIP-*` skills.

Two lessons stand out:
- **The Critical was introduced by the fix, not present before.** Removing `git add -A`
  silently removed the only thing committing post-merge fixes.
- **The first clean-tree check could never pass.** Both are the kind of defect that only a
  reader tracing the full flow catches.

As with every prompt change here, no automated harness covers this surface. Per `docs/TRIP.md` §
Integration checks, the real confirmation is the next live TRIP run on a downstream project.
