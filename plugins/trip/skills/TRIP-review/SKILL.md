---
name: TRIP-review
description: Review code following project standards (manual fallback/audit path)
disable-model-invocation: true
argument-hint: "version or feature to review"
---

# Review Mode

You are now in **code review mode** for **this project**.

This is the **manual fallback/audit path**: normal reviews happen via the Codex loop inside `TRIP-2-implement`. Use this skill to audit a past version, review unplanned work, or replace the Codex loop when it is unavailable.

Review: $ARGUMENTS

## Prerequisites

Read before reviewing:
0. Read `docs/TRIP.md` — this project's TRIP profile: name, type, main branch, version file, week anchor, the lint/typecheck/test commands, and the project-specific sections this skill refers to. It is written by `TRIP-init`. If it is missing, run `/TRIP-init` first (or, for a project set up before TRIP became a plugin, `/TRIP-upgrade`).
1. `docs/archi/index.md`, then the wiki pages covering the area this change touches — verify architectural compliance. (Projects that have not run `/wiki-migrate` yet still have a monolithic `docs/ARCHI.md`; read that instead.)
2. Related plan in `docs/1-plans/`
3. Related changelog in `docs/2-changelog/`
4. docs/3-code-review/checklist.md — **single source of truth** for review criteria, severity classification, and approval gate. Written into the project by `TRIP-init` and tailored to this codebase.

---

## Graph-Assisted Analysis

Before walking the checklist, run the code-review-graph MCP tools for risk-scored, structural context:
1. `detect_changes_tool` — risk-scored change analysis.
2. `get_affected_flows_tool` — impacted execution paths.
3. `query_graph_tool` with pattern `tests_for` on each changed function — test coverage status.
4. `get_impact_radius_tool` — blast radius for the change.

Combine these findings with the conventions documented in the wiki while walking the checklist below — the graph tells you what changed and what it touches; the wiki tells you whether that's the right way to do it here.

If the graph and the wiki disagree, the code is right and the wiki has drifted: note it, and run `/wiki-ingest` afterwards rather than reviewing against a stale page.

## Apply the Checklist

Walk every section of `checklist.md` against the change. Tick passing items. Failing items become findings classified by the severity scale in that file. Approval requires the gate at the bottom of `checklist.md`.

Do not copy the checklist into output — link to it.

---

## Create Review File

Save to `docs/3-code-review/CR_wa_vx.y.z.md` (a=project week, x.y.z=version).

Render the skeleton from `docs/3-code-review/cr-template.md`:
1. Copy the markdown block from that file.
2. Replace every `<angle-bracket placeholder>` with concrete content.
3. Tick `[x]` for passing checklist items; leave unchecked with a one-line caveat otherwise.

Every checklist item must be ticked or annotated — a silent unchecked box is a red flag.
