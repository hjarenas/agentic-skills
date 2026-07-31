---
name: TRIP-hotfix
description: Urgent fix bypassing full TRIP workflow
disable-model-invocation: true
argument-hint: "what is broken in production?"
---

# Hotfix Mode

You are now in **hotfix mode** - a streamlined workflow for urgent production fixes.

> **Warning**: Only use this for genuine emergencies. For regular bugs, use the full TRIP workflow (`TRIP-1-plan` → `TRIP-2-implement`).

## Your Task

Hotfix: $ARGUMENTS

---

## Step 1: Assess Urgency

Before proceeding, confirm this is a genuine hotfix:

**Use the `AskUserQuestion` tool** to confirm urgency:

- **Question**: "Is this a production-critical issue that cannot wait for the normal TRIP workflow?"
- **Options**: "Yes — critical issue" (security vulnerability, data corruption, service outage, or critical user-facing bug), "No — regular bug" (redirect to `TRIP-1-plan` for proper workflow)

**If "No"**: Redirect to `TRIP-1-plan` for proper workflow.

**If "Yes"**: Proceed with hotfix.

---

## Step 2: Create Hotfix Branch

```bash
git checkout main && git pull
git checkout -b hotfix/[short-description]
```

---

## Step 3: Minimal Investigation

First, read `docs/archi/index.md` and open the wiki pages covering the failing area (un-migrated projects: read `docs/ARCHI.md` in full). Then use the code-review-graph MCP tools to find the relevant code fast — `semantic_search_nodes` for the symptom/component, `query_graph` (`callers_of`/`imports_of`) to trace it, `get_impact_radius` to see what else touches it — instead of manually grepping; fall back to Grep/Read only for what the graph doesn't cover.

Quickly identify:

1. **Root cause** (1-2 sentences)
2. **Affected files** (list)
3. **Fix approach** (brief)

No formal plan document needed.

---

## Step 4: Implement Fix

- Focus only on the fix - no refactoring, no "while I'm here" improvements
- Minimal changes to resolve the issue
- Follow existing patterns from the codebase

---

## Step 5: Quick Verification

- Manually test the fix
- Run relevant tests only: `[test command] [affected files]`
- Confirm the issue is resolved
- If the hotfix touches a cloud or infrastructure boundary, verify it against the
  real environment per `docs/TRIP.md` § Integration checks — including any
  project-specific verification skill named there — instead of trusting local
  tests alone. A deploy pipeline typically only reveals the next latent failure
  once the earlier steps pass, so an unverified "fix" can still fail in CI after
  a long round trip

---

## Step 6: Version & Changelog

### Version Bump

Increment **patch** version only (x.y.Z+1) in version file.

### Minimal Changelog Entry

Add to top of `docs/2-changelog/changelog_table.md`:

```markdown
| `x.y.z` | W | hotfix: [brief description] |
```

Add to Changelog Summary:

```markdown
- **vX.Y.Z (Hotfix - Week W, DD-MM-YYYY)**:
  - **Issue**: [What was broken]
  - **Fix**: [What was done]
  - **Root Cause**: [Brief explanation]
```

---

## Step 7: Commit

```bash
git add -A && git commit -m "hotfix: [brief description]"
```

---

## Step 8: Merge & Tag

```bash
git checkout main
git merge hotfix/[short-description]
git tag vx.y.z
git push && git push --tags
git branch -d hotfix/[short-description]
```

---

## Step 9: Post-Hotfix

After the immediate crisis is resolved:

1. **Document**: Create a brief incident report in `docs/6-memo/` if significant
2. **Follow-up**: If deeper fixes are needed, create a proper TRIP plan
3. **Retrospective**: Consider what could prevent similar issues

---

## What This Workflow Skips

Compared to full TRIP:

- No interactive discovery questions
- No formal plan document
- No full code review checklist
- No tutorial generation
- No `/wiki-ingest` (unless the fix changed the architecture)
- No README update (unless relevant)

These are acceptable trade-offs for genuine emergencies only.
