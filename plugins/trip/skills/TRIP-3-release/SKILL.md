---
name: TRIP-3-release
description: Release a completed implementation - version, code review promotion, changelogs, docs, commit, pull request, tag
argument-hint: "plan file or feature label"
---

# Release Mode

You are now in **release mode** for **this project**.

Release: $ARGUMENTS

## Operating model

Read and obey [the agent routing contract](../../references/agent-routing.md). Parse routing
overrides from `$ARGUMENTS`, then treat the remainder as the plan or feature label. You are a
pure orchestrator. Dispatch all verification and release mutations; do none yourself.

This skill runs after `TRIP-2-implement` has converged (implementation done, testing gate green, Codex code review `APPROVED` or explicitly skipped). It is normally chained from TRIP-2 in the same session, but can be invoked standalone in a fresh session.

Continue inside the feature-branch worktree created for this flow by `TRIP-1-plan`, not the
primary working tree. Steps 1-10 and every `release-worker` or `release-verifier` dispatch must
carry that worktree path explicitly as their working directory. A standalone invocation locates
it using the same plan-commit-to-branch match in `git worktree list` described by
`TRIP-2-implement` Step 0; it must not reconstruct the path from naming conventions.

---

## Prerequisites

- `docs/TRIP.md` exists and has been read (it carries the version file, week anchor, main branch,
  and commands every step below needs). If it is missing, stop immediately and tell the user to
  run `/TRIP-init` first (or `/TRIP-upgrade` for a project set up before TRIP became a plugin) —
  do not improvise a profile inline.
- Implementation complete and user-confirmed.
- Testing gate green: affected unit tests pass.
- Codex code review converged (`APPROVED`), or explicitly skipped by the user.
- Lint and type-check/build green.
- Local infra required by pre-commit/pre-push hooks (`docs/TRIP.md` § Integration checks), if
  any, is running — a hook-triggered full test/E2E run can otherwise fail deep into Step 10's
  push instead of here, where it is cheaper to catch.

### Standalone verification (fresh session, not chained from TRIP-2)

If this skill was NOT chained from a TRIP-2 session, dispatch `test-worker` to verify before any release step:

```bash
# Commands come from docs/TRIP.md § Commands — read it first.
<lint command — docs/TRIP.md § Commands>
<typecheck command — docs/TRIP.md § Commands>
<test command — docs/TRIP.md § Commands> <pattern-from-the-plan's-Test-Impact-section>
```

All must be green. Also verify a stored Codex review exists for the given plan path/label under `.codex-bridge/` (see Step 3 below); if absent, treat as the skipped-Codex fallback (manual CR) and say so explicitly in the CR.

Any failure blocks the release — fix or return to `TRIP-2-implement` first.

---

## Steps 1-8: Prepare release artifacts

`release-worker` (`codex-release` for `codex-bridge`) owns every file edit and command in these
steps, dispatched with the plan, `docs/TRIP.md`, the approved review, and the steps below. When
the artifacts are complete, dispatch `release-verifier` (`codex-release-verify`) read-only to
check versions, placeholders, changelog links, wiki lint, README, branch safety, and the full
diff. Route corrections back to `release-worker`, then re-verify.

**These steps are not one serial dispatch.** Release is the tail of every flow and the phase most
often left waiting on a single worker grinding through eight unrelated edits, with the wiki
update (Step 7) usually dominating. Most of the steps write disjoint files, so schedule them as:

1. **Step 1 alone, first.** It writes nothing and computes the date and project week every other
   step needs. Carry its output explicitly into each dispatch below.
2. **Then Steps 2, 3, 5-8 as three parallel `release-worker` dispatches**, split by write path:
   - version files and lockfiles (Step 2) + `README.md` (Step 8);
   - `docs/3-code-review/` (Step 3) + `docs/2-changelog/` (Steps 5 and 6, same worker: the table
     entry links the changelog file, so one worker writing both keeps them consistent);
   - `docs/archi/` via `/wiki-ingest` (Step 7) — usually the long pole, so start it in this round
     rather than after.
3. **Then Step 4**, the commit message, which describes what the other steps produced.

All three run in the one feature worktree, so give each a **lane** (`agent-routing.md` §Lanes) —
the path sets listed above are already disjoint, so state them as lanes and dispatch. Staging and
committing belong to Step 9's single dispatch, after all three have reported. If any dispatch
reports work it could only do outside its lane, serialize the remainder rather than widening a
lane mid-flight: a corrupted release artifact costs more than a slow release.

Run `release-verifier` once, after all of Steps 1-8 have landed, over the combined diff. Verifying
per-worker would miss the cross-file consistency (version vs changelog vs README) that is the main
thing worth checking.

### Step 1: Get Current Date/Week

`<week anchor — docs/TRIP.md § Project>` must be in `YYYY-MM-DD` format for `date -d` to parse
reliably. Validate before using it — a malformed anchor (e.g. a legacy profile stored as
`DD-MM-YYYY`) should fail here with a clear message, not cascade into a bash arithmetic error:

```bash
WEEK_ANCHOR="<week anchor — docs/TRIP.md § Project>"
date -d "$WEEK_ANCHOR" >/dev/null || { echo "docs/TRIP.md week anchor '$WEEK_ANCHOR' is not YYYY-MM-DD — fix it in docs/TRIP.md before continuing"; exit 1; }
date '+%d-%m-%Y %H:%M' && echo "Project week: $(( ( $(date +%s) - $(date -d "$WEEK_ANCHOR" +%s) ) / 604800 + 1 ))"
```

Use the project week in all subsequent steps.

### Step 2: Version Update

- If not already done in the plan phase, propose new SemVer version (x.y.z)
- Update version in `<version file — docs/TRIP.md § Project>`
- Change only the version field in this file

### Step 3: Promote Code Review

Now that week (`a`) and version (`x.y.z`) are known:

1. Retrieve the stored review — invoke `codex-code-review show <plan-path>`, or read it directly:
   ```bash
   ls .codex-bridge/
   ```
   The key is the plan path with `/` replaced by `__` (e.g. `docs__1-plans__F_0.4.0_feature.plan.md.md`).

2. Content source:
   - **Multi-round loop**: the stored review is the synthesized one, ending in `PROMOTION_READY`. Strip the sentinel.
   - **Turn 1 convergence**: the stored review is the full review already.
   - **Skipped Codex**: write CR from `docs/3-code-review/cr-template.md` with body "Code review skipped — trivial change." Verdict: `APPROVED with observations`.

3. Replace `<x.y.z>` with actual version. Fill any remaining `<...>` placeholders.

4. Save to `docs/3-code-review/CR_wa_vx.y.z.md`.

5. Verify: no `<...>` placeholders, no `PROMOTION_READY`, version matches version file.

### Step 4: Commit Message

Propose a one-line commit message.

### Step 5: Changelog File

Create `docs/2-changelog/wa_vx.y.z.md` (a=project week, x.y.z=version):

```markdown
# Changelog - Week a, DD-MM-YYYY, V. x.y.z

**Release Date**: Week a, DD-MM-YYYY at HH:MM
**Version**: x.y.z (previously x0.y0.z0)
**Object**: the commit message
**Code review**: `docs/3-code-review/CR_wa_vx.y.z.md` (Codex loop, N rounds -> verdict)

## Changes

[Describe what changed]
```

### Step 6: Changelog Table

Add entry on top of `docs/2-changelog/changelog_table.md`:

```markdown
| `x.y.z` | a | the commit message |
```

Also add a summary entry in the Changelog Summary section.

### Step 7: Architecture Update

Fold this release into the architecture wiki by invoking the `wiki-ingest` skill with the
version you just bumped to:

```
wiki-ingest <x.y.z>
```

See that skill for what it does with the changelog and diff. Before invoking it, cross-check with
the code-review-graph MCP tools — `get_architecture_overview` and `list_communities` — so the
ingest knows about any module the diff alone would not reveal.

Invoke the `wiki-lint` skill with `--fix` and fix anything cheap. Call it by name, not by
constructing a path through `${CLAUDE_PLUGIN_ROOT}` — each plugin installs in its own cache
directory, so a path built from this skill's root never reaches `trip-wiki`.

Pages split rather than compact, so a page growing large is a `wiki-lint` finding, not a release
blocker.

**Un-migrated projects** still have a monolithic `docs/ARCHI.md`. For those: read
`docs/ARCHI-rules.md`, update `docs/ARCHI.md` following it, and consider running
`/wiki-migrate` to stop paying this cost every release.

If `docs/TRIP.md` § Tutorials says tutorials are enabled, see `tutorial-step.md` in this skill's
directory for Step 8 (and renumber the steps that follow: README becomes 9, Commit 10, and so on).
Otherwise skip straight to:

### Step 8: README Update

Update `README.md` with the new version number.
Also update relevant sections whenever needed.

---

After completing all documentation steps in a standalone release run, **use the
`AskUserQuestion` tool** to ask:

- **Question**: "All documentation steps are complete. Ready to commit and open the pull request?"
- **Options**: "Yes, open the PR" (commit on the feature branch, push, open PR), "Not yet" (review changes first)

Suppress this prompt when this skill runs as a child of `TRIP-auto`; the parent has already
authorized proceeding through the release-documentation steps without further confirmation.

In a standalone run, **ONLY after user selects "Yes"**, proceed:

## Step 9: Commit (on the feature branch)

Dispatch this step to `release-worker`, then have `release-verifier` confirm the commit contains
only intended release work and remains on the feature branch.

```bash
git add -A && git commit -m "<commit message from Step 4>"
```

**Important**: Only use the commit message. Do NOT add Co-Authored-By or any other trailer. **Do not tag, do not merge, do not touch the main branch** — the release lands through a pull request.

## Step 10: Push the branch and open the pull request

**First, check the branch is not stale against the main branch.** A TRIP flow can run for hours
while other work merges, and the first anyone learns of it is usually a conflicted PR the user has
to point out. Have `release-worker` fetch and compare before pushing:

```bash
git fetch origin <main branch — docs/TRIP.md § Project>
git rev-list --count HEAD..origin/<main branch>          # commits on main we don't have
git merge-tree --write-tree HEAD origin/<main branch> >/dev/null 2>&1 || echo "WOULD CONFLICT"
```

If the count is 0, proceed. If main has moved but the trees merge cleanly, proceed and note it in
the PR description — GitHub will merge it. On `WOULD CONFLICT`, report `RELEASE_BLOCKED` with the
conflicting paths and hand them back through the flow: an `implementer` lane scoped to those files,
then a re-run of the testing gate, then return here. That is the route `phase-scheduling.md` uses
for a phase merge conflict, and it applies for the same reason — a resolution rewrites reviewed,
gate-verified content, so it earns review and a gate of its own rather than a quick rebase.

Then dispatch push and PR creation to `release-worker`. Dispatch `release-verifier` to inspect the
resulting PR metadata and URL before reporting it.

```bash
git push -u origin <feature-branch>
gh pr create --base <main branch — docs/TRIP.md § Project> --title "<commit message from Step 4>" --body-file <generated-description>
```

Write the PR description so the reviewer can approve **without reading every file** — it must carry a summary of what was done. Use the PR-description template from the `TRIP-auto` skill (Phase 4): Summary, plan/version/changelog links, what changed by area, decisions made along the way, verification (testing gate + Codex review rounds/verdicts), and an "After merging" checklist (tag `vx.y.z` + push tag, deployment follow-ups such as the deploy workflow triggering on merge).

Report the PR URL to the user. **Do not merge the PR yourself.**

## Step 11: Post-merge (after the user approves and merges)

The user merges with **"Rebase and merge"** (or squash) to keep linear history. Then:

**This is the one cwd exception in the flow.** Switch back to the primary working tree before
running any command below. Update the main branch there, then remove the feature worktree from
the primary tree; Git cannot remove the worktree that is the current working directory. Only
after the worktree is removed can the checked-out feature branch be deleted.

```bash
git checkout <main branch — docs/TRIP.md § Project> && git pull
git worktree remove ../<repo>-<slug>-<suffix>
git tag vx.y.z && git push --tags
git branch -d <feature-branch>
```

If the merge to the main branch triggers a deployment workflow, watch it and report the outcome as part of closing the release.
