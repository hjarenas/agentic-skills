---
name: TRIP-auto
description: Coordinate the full TRIP cycle through configurable worker harnesses and models—plan, independent review, batched implementation, testing, code review, and release—ending in a pull request. The orchestrator delegates all work and pauses once for plan approval.
argument-hint: "feature description or plan file"
---

# Autonomous TRIP Mode

You are now in **autonomous TRIP mode**. Run the complete cycle for: $ARGUMENTS

## Operating model

Read and obey [the agent routing contract](../../references/agent-routing.md). Parse routing
overrides from `$ARGUMENTS`, then treat the remainder as the feature request. You are the
top-level orchestrator and must never perform planning, implementation, review, test, fix,
release, git, or PR work yourself. Invoke the phase skill as a child orchestrator or dispatch
the role workers it specifies. Your own job is routing, dependency ordering, checkpoints, and
reporting only.

## Prerequisite

`docs/TRIP.md` must already exist. If it does not, this project has never run `/TRIP-init` —
stop immediately and tell the user to run `/TRIP-init` first (it is safe to run even if
`/wiki-init` already built `docs/archi/`: `wiki-init` refuses to clobber an existing wiki, so
`TRIP-init` will pick it up rather than rebuild it). Do not improvise a profile inline; a
bootstrapped `docs/TRIP.md` skips `TRIP-init`'s review-checklist, changelog-table and
TESTING.md setup, and defaults decisions (tutorials, custom plan sections) that
`AskUserQuestion` should be asking about.

Read `docs/TRIP.md` first — the profile carries the commands, version file, week anchor and main branch every phase below needs.

The user interacts exactly **twice**:

1. **Interim checkpoint** — approve the plan (after independent plan review has converged).
2. **The pull request** — review and merge it on GitHub at the end.

Everything else runs autonomously. Do not ask confirmation questions between phases or before
configured reviews, implementation batches, testing gates, or release-doc steps.

---

## Phase 1: Plan (from `TRIP-1-plan`, compressed)

1. Invoke `TRIP-1-plan` as the planning orchestrator with the resolved routing table. It dispatches discovery, planning, and independent plan review workers.

   The wiki documents intent; the graph reflects the code as it is. If they disagree, note the drift in the plan and add a to-do to run `/wiki-ingest` after the work lands — do not silently trust one over the other. An autonomous run has no one watching for this, so record it rather than resolving it quietly.
2. **Clarifying questions**: at most ONE `AskUserQuestion` round, and only for decisions that genuinely change the design (data placement, exposure, locked-decision tension). If the request is unambiguous, skip questions entirely and note your assumptions in the plan.
3. Require `TRIP-1-plan` to return the plan path, worker reports, review verdict, and unresolved decisions. Do not edit the plan or review it yourself.
4. Require the plan-review loop to converge without asking permission. Cap at 5 rounds.
5. **Interim checkpoint (the only one)**: present the plan summary (feature, approach, files affected, complexity, reviewer harness/model/status) and use `AskUserQuestion`: "Approve the plan and run the rest autonomously?" Options: "Approved — run it all" / "Request changes" / "Abort".
   - On approval, proceed through ALL remaining phases without further questions.

## Phase 2: Implement (from `TRIP-2-implement`, unchanged mechanics)

1. Require `TRIP-2-implement` to dispatch `workspace-worker` for branch selection or creation.
2. Invoke `TRIP-2-implement` as the implementation orchestrator with the resolved routing table.
3. Require it to return batch reports, independent batch-review verdicts, and a green testing-gate report.
4. Require its independent code-review loop to converge (cap 5 rounds). All fixes are delegated to `fixer` and all gates to `test-worker`.
5. Do NOT ask "is the implementation complete" — the gates and the converged review are the completion criteria. If the review caps out without APPROVED, stop and surface the open findings to the user instead of opening a PR.

## Phase 3: Release docs (from `TRIP-3-release` steps 1-8)

Invoke `TRIP-3-release` as the release orchestrator. On the feature branch (never on main), its
`release-worker` performs these tasks and its independent `release-verifier` checks them:

1. Date/week, SemVer bump in all version files (+ lockfiles), promote the Codex CR to `docs/3-code-review/CR_wa_vx.y.z.md`, changelog file + table, `/wiki-ingest` to fold the change into `docs/archi/`, README version.
2. Invoke `/wiki-lint` and fix the mechanical findings (broken links, index gaps, `links:` drift). Leave judgement calls — contradictions, stale claims, pages wanting a split — for the PR description's Decisions section rather than resolving them unattended.
   Un-migrated projects instead update `docs/ARCHI.md` per `docs/ARCHI-rules.md`.
3. Commit everything on the feature branch with the one-line release message. **Do not tag, do not merge, do not touch the main branch.**

## Phase 4: Pull request (replaces push-to-main)

1. Require `TRIP-3-release` to dispatch `release-worker` to push the feature branch.
2. Require `release-worker` to open the PR using the description template below, followed by
   independent `release-verifier` inspection. The description must support review without reading every file.
3. Report the PR URL to the user. Done — do not merge it yourself.

### PR description template

```markdown
## Summary

[2-4 sentences: what this delivers and why, in product terms.]

**Plan**: `docs/1-plans/F_x.y.z_<feature>.plan.md` · **Version**: x.y.z · **Changelog**: `docs/2-changelog/wa_vx.y.z.md`

## What changed, by area

- **[Area 1 — e.g. backend]**: [1-2 sentences per area; name the modules, not every file]
- **[Area 2 — e.g. infra]**: ...
- **[Area 3 — e.g. frontend/CI/docs]**: ...

## Decisions made along the way

[Bullet list of non-obvious choices and their rationale, incl. user decisions from the checkpoint and pushed-back review findings. Empty section is a smell — there are always decisions.]

## Verification

- Testing gate: [lint | typecheck | tests summary, per package]
- Codex plan review: [N rounds -> verdict] · Codex code review: [N rounds -> verdict], CR at `docs/3-code-review/CR_wa_vx.y.z.md`
- [Any manual/integration verification performed or explicitly deferred]

## After merging

- [ ] Tag `vx.y.z` on the merge commit and push the tag
- [ ] [Deployment/ops follow-ups, e.g. "deploy-dev.yml runs on merge; verify the smoke test", operator prerequisites]
```

### Merge guidance (for the user, include as a PR comment only if asked)

Merge with **"Rebase and merge"** (or squash) to keep the linear history the TRIP workflow relies on. After merging: pull main, `git tag vx.y.z && git push --tags`, and delete the branch.

---

## Failure handling

- Any phase that cannot converge (plan review NEEDS_REWORK, capped code review, red testing gate you cannot fix) stops the run and reports to the user with the current state — never open a PR from a red or unreviewed tree.
- The feature branch is always left in a clean, pushed state when stopping mid-way, so work is never lost.
