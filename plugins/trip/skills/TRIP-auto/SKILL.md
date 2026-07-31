---
name: TRIP-auto
description: Run the full TRIP cycle end to end autonomously - plan, Codex plan review, implement in batches, testing gate, Codex code review, release docs - ending in a pull request for the user to review instead of a push to main. One interim checkpoint (plan approval); everything else runs without questions.
argument-hint: "feature description or plan file"
---

# Autonomous TRIP Mode

You are now in **autonomous TRIP mode**. Run the complete cycle for: $ARGUMENTS

Read `docs/TRIP.md` first — the profile carries the commands, version file, week anchor and main branch every phase below needs.

The user interacts exactly **twice**:

1. **Interim checkpoint** — approve the plan (after the Codex plan review has converged).
2. **The pull request** — review and merge it on GitHub at the end.

Everything else runs autonomously. Do not ask confirmation questions between phases; do not ask whether to run Codex reviews (always run them); do not ask before starting implementation batches, the testing gate, or the release-doc steps.

---

## Phase 1: Plan (from `TRIP-1-plan`, compressed)

1. Read `docs/archi/index.md` plus the pages covering the target area, and query the code-review-graph MCP tools (`get_minimal_context`, `semantic_search_nodes`, `get_impact_radius`) for the feature's current code-level structure — see `TRIP-1-plan`'s Prerequisites for the pattern. Projects that have not run `/wiki-migrate` still have a monolithic `docs/ARCHI.md`; read that in full instead.

   The wiki documents intent; the graph reflects the code as it is. If they disagree, note the drift in the plan and add a to-do to run `/wiki-ingest` after the work lands — do not silently trust one over the other. An autonomous run has no one watching for this, so record it rather than resolving it quietly.
2. **Clarifying questions**: at most ONE `AskUserQuestion` round, and only for decisions that genuinely change the design (data placement, exposure, locked-decision tension). If the request is unambiguous, skip questions entirely and note your assumptions in the plan.
3. Write the plan document per the `TRIP-1-plan` template to `docs/1-plans/F_x.y.z_<feature>.plan.md`.
4. Run the Codex plan review loop by invoking the `codex-plan-review` skill, to convergence and without asking permission. Cap at 5 rounds; address findings critically, and pass what you fixed (and what you pushed back on) as notes on every resume — each Codex turn is a fresh run and the notes are its only memory.
5. **Interim checkpoint (the only one)**: present the plan summary (feature, approach, files affected, complexity, Codex status) and use `AskUserQuestion`: "Approve the plan and run the rest autonomously?" Options: "Approved — run it all" / "Request changes" / "Abort".
   - On approval, proceed through ALL remaining phases without further questions.

## Phase 2: Implement (from `TRIP-2-implement`, unchanged mechanics)

1. `git checkout -b feat/<short-description>` (or `fix/`).
2. Batch the plan and delegate to the `codex-implement` skill exactly as `TRIP-2-implement` prescribes: smallest-green batches, delta review after each, fix problems yourself, micro-gate (lint + typecheck), `git add -A` checkpoint, corrections carried into the next batch as notes.
3. Final pass over the full diff, then the full testing gate (lint, typecheck, affected tests, integration impact, author missing tests).
4. Run the `codex-code-review` loop to convergence (cap 5 rounds), fixing findings, passing notes on each resume, and re-running the gate between rounds. Synthesize the consolidated review if it took more than one round.
5. Do NOT ask "is the implementation complete" — the gates and the converged review are the completion criteria. If the review caps out without APPROVED, stop and surface the open findings to the user instead of opening a PR.

## Phase 3: Release docs (from `TRIP-3-release` steps 1-8)

On the feature branch (never on the main branch):

1. Date/week, SemVer bump in all version files (+ lockfiles), promote the Codex CR to `docs/3-code-review/CR_wa_vx.y.z.md`, changelog file + table, `/wiki-ingest` to fold the change into `docs/archi/`, README version.
2. Invoke `/wiki-lint` and fix the mechanical findings (broken links, index gaps, `links:` drift). Leave judgement calls — contradictions, stale claims, pages wanting a split — for the PR description's Decisions section rather than resolving them unattended.
   Un-migrated projects instead update `docs/ARCHI.md` per `docs/ARCHI-rules.md`.
3. Commit everything on the feature branch with the one-line release message. **Do not tag, do not merge, do not touch the main branch.**

## Phase 4: Pull request (replaces push-to-main)

1. Push the feature branch: `git push -u origin <branch>`.
2. Open the PR with `gh pr create --base <main branch — docs/TRIP.md § Project>` using the description template below. The description must let the reviewer approve WITHOUT reading every file.
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
