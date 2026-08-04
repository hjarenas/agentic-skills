---
name: TRIP-3-release
description: Release a completed implementation - version, code review promotion, changelogs, docs, commit, tag, ff-merge, push
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

---

## Prerequisites

- Implementation complete and user-confirmed.
- Testing gate green: affected unit tests pass.
- Codex code review converged (`APPROVED`), or explicitly skipped by the user.
- Lint and type-check/build green.

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

Dispatch `release-worker` with the plan, `docs/TRIP.md`, approved review, and Steps 1-8 below.
It owns every file edit and command in these steps. When it reports completion, dispatch
`release-verifier` read-only to check versions, placeholders, changelog links, wiki lint, README,
branch safety, and the full diff. Route corrections back to `release-worker`, then re-verify.

### Step 1: Get Current Date/Week

Run this command to get date and project week:

```bash
date '+%d-%m-%Y %H:%M' && echo "Project week: $(( ( $(date +%s) - $(date -d '<week anchor — docs/TRIP.md § Project>' +%s) ) / 604800 + 1 ))"
```

Use the project week in all subsequent steps.

### Step 2: Version Update

- If not already done in the plan phase, propose new SemVer version (x.y.z)
- Update version in `<version file — docs/TRIP.md § Project>`
- Do not modify anything else in this file

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

It reads the changelog and the diff for that version, updates the affected pages, adds pages for
anything new, splits any page that outgrew the size limit, fixes cross-references, and writes
`docs/archi/log/v<x.y.z>.md`.

Before ingesting, cross-check with the code-review-graph MCP tools — `get_architecture_overview`
and `list_communities` — so the ingest knows about any module the diff alone would not reveal.

Then invoke the `wiki-lint` skill and fix anything cheap. Do not try to call its script by path
from here — each plugin is installed in its own cache directory, so `${CLAUDE_PLUGIN_ROOT}` from
this skill does not reach `trip-wiki`. Invoking the skill is the supported way across plugins.

There is no size warning to heed here: pages are split, not compacted, so the wiki does not have
a token ceiling to breach. A page that grew too large is a lint finding, not a release blocker.

**Un-migrated projects** still have a monolithic `docs/ARCHI.md`. For those: read
`docs/ARCHI-rules.md`, update `docs/ARCHI.md` following it, and consider running
`/wiki-migrate` to stop paying this cost every release.

<!-- Tutorials: include this step only if docs/TRIP.md § Tutorials says they are enabled.
     When enabled, renumber the steps that follow (README becomes 9, Commit 10, and so on).
### Step 8: Tutorial

Create `docs/5-tuto/tuto_x.y.z.md` explaining the core principle.

**User context for tutorials**:

- Level: <level — docs/TRIP.md § Tutorials>
- Learning focus: <focus — docs/TRIP.md § Tutorials>
- Style: <style — docs/TRIP.md § Tutorials>
-->

### Step 8: README Update

Update `README.md` with the new version number.
Also update relevant sections whenever needed.

---

After completing all documentation steps, **use the `AskUserQuestion` tool** to ask:

- **Question**: "All documentation steps are complete. Ready to commit and open the pull request?"
- **Options**: "Yes, open the PR" (commit on the feature branch, push, open PR), "Not yet" (review changes first)

**ONLY after user selects "Yes"**, proceed:

## Step 9: Commit (on the feature branch)

Dispatch this step to `release-worker`, then have `release-verifier` confirm the commit contains
only intended release work and remains on the feature branch.

```bash
git add -A && git commit -m "<commit message from Step 4>"
```

**Important**: Only use the commit message. Do NOT add Co-Authored-By or any other trailer. **Do not tag, do not merge, do not touch the main branch** — the release lands through a pull request.

## Step 10: Push the branch and open the pull request

Dispatch push and PR creation to `release-worker`. Dispatch `release-verifier` to inspect the
resulting PR metadata and URL before reporting it.

```bash
git push -u origin <feature-branch>
gh pr create --base <main branch — docs/TRIP.md § Project> --title "<commit message from Step 4>" --body-file <generated-description>
```

Write the PR description so the reviewer can approve **without reading every file** — it must carry a summary of what was done. Use the PR-description template from the `TRIP-auto` skill (Phase 4): Summary, plan/version/changelog links, what changed by area, decisions made along the way, verification (testing gate + Codex review rounds/verdicts), and an "After merging" checklist (tag `vx.y.z` + push tag, deployment follow-ups such as the deploy workflow triggering on merge).

Report the PR URL to the user. **Do not merge the PR yourself.**

## Step 11: Post-merge (after the user approves and merges)

The user merges with **"Rebase and merge"** (or squash) to keep linear history. Then:

```bash
git checkout <main branch — docs/TRIP.md § Project> && git pull
git tag vx.y.z && git push --tags
git branch -d <feature-branch>
```

If the merge to the main branch triggers a deployment workflow, watch it and report the outcome as part of closing the release.
