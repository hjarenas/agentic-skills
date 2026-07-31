---
name: TRIP-1-plan
description: Plan a new feature following project standards
argument-hint: "describe the feature you want to build"
---

# Planning Mode

You are now in **planning mode** for **this project**.

## Prerequisites - Read First

Before creating any plan:

0. Read `docs/TRIP.md` — this project's TRIP profile: name, type, main branch, version file, week anchor, the lint/typecheck/test commands, and the project-specific sections this skill refers to. It is written by `TRIP-init`. If it is missing, run `/TRIP-init` first (or, for a project set up before TRIP became a plugin, `/TRIP-upgrade`).
1. Read `docs/archi/index.md` in full, then open the wiki pages covering the area this feature touches and follow their `[[links]]` one hop. Do not read the whole wiki — the index exists so you don't have to. (Projects that have not run `/wiki-migrate` still have a monolithic `docs/ARCHI.md`; read that in full instead.)
2. Query the code-review-graph MCP tools for the feature's actual code-level structure: `get_minimal_context(task="<feature summary>")` first, then `semantic_search_nodes` for modules matching the feature's keywords and `get_impact_radius`/`query_graph` (`callers_of`/`imports_of`) on anything the feature will touch. Use `detail_level="minimal"`; escalate only if insufficient.

The wiki documents intent; the graph reflects the code as it actually is. If they disagree (undocumented module, stale pattern), note the drift in the plan rather than silently trusting one over the other — and add a to-do to run `/wiki-ingest` after the work lands.

## Your Task

Plan the following feature: $ARGUMENTS

---

## Step 1: Discovery & Clarification (Interactive)

**Do NOT start writing a plan immediately.** First, engage in a discovery conversation to fully understand the user's intent.

### 1.1 Initial Understanding

After reading the feature request, summarize your understanding in 2-3 sentences, then **use the `AskUserQuestion` tool** to present clarifying questions with structured options.

Frame questions around:

- **Scope**: What's included vs excluded?
- **Behavior**: How should it work from the user's perspective?
- **Constraints**: Any technical limitations, deadlines, or dependencies?
- **Priority**: What's most important if trade-offs are needed?

For each question, provide 2-4 concrete options based on your analysis of the codebase and the feature request. Always let the user provide custom input via the built-in "Other" option.

After the user answers, proceed **directly to writing the plan** (Step 2) — no approach-confirmation question. Ask a follow-up round with `AskUserQuestion` only if a blocking ambiguity remains (**maximum 3 rounds total**; if still unclear, summarize what you know and proceed with noted assumptions).

---

## Step 2: Plan Document Creation

Once understanding is confirmed, create the plan document.

### File Naming

Depending on the feature (major, minor, patch), propose a new version using SemVer (x.y.z) and create:
`docs/1-plans/F_[version]_[feature-name].plan.md`

### Required Sections

```markdown
# [Feature Name] Implementation Plan

## Overview

[2-4 sentences describing the feature and its purpose]

## Problem Statement (if applicable)

[Current limitations/issues this feature addresses]

## Solution Architecture

[High-level design approach]

## Implementation Details

### 1. [Component/Module/File Name]

**File**: `path/to/file`

[Detailed description of changes needed]

**Current state** (if modifying existing):
[Describe what currently exists]

**Modifications**:

- Specific change 1 (around line X)
- Specific change 2 (around line Y)

### 2. [Next Component/Module/File]

[Continue with same pattern]

## Technical Considerations

Project-specific technical concerns: use the bullets from docs/TRIP.md § Plan considerations, plus the ones below that apply.

- **Pattern Usage**: Which existing patterns to follow (cite the wiki page)
- **[Concern 1]**: [Description]
- **[Concern 2]**: [Description]
- **Edge Cases**: [Relevant edge cases for this feature]

## Files to Modify/Create

[Comprehensive numbered list with purposes]

1. `path/to/file1` (modify) - Purpose description
2. `path/to/file2` (new) - Purpose description

## Type Definitions (if applicable)

[New types, interfaces, structs, or modifications to existing ones]

## Performance & Cost Impact (if applicable)

[Expected performance implications]

## Backward Compatibility (if applicable)

[Migration strategy if needed]

## Test Impact

[2-5 bullets: which existing tests the change affects, what new logic will need tests, whether an integration/E2E check applies. No test code — the TRIP-2 testing gate consumes this section.]

## To-dos

### Phase 1: [Phase Name] (if multiple phases are needed) or simply skip title if only one phase is needed

- [ ] Task description
- [ ] Another task

### Phase 2: [Phase Name] (if applicable)

- [ ] Task description
- [ ] Another task

**Note**: For simple plans, a single phase is sufficient. Split into multiple phases only for complex features requiring sequential implementation.

**Note**: Do NOT write test code during planning — the Test Impact section above only names what the TRIP-2 testing gate will run and author.
```

## Quality Standards

- **Zero Ambiguity**: Every step must be clear and actionable
- **File-Level Specificity**: List exact files and functions to modify
- **Architecture Alignment**: Must conform to the patterns documented in `docs/archi/`, cross-checked against the graph's current callers/dependents where relevant
- **Risk Assessment**: Highlight potential failure points

---

## Step 3: Codex Second-Opinion Review

Before the user sees the plan, run the Codex plan review loop.

### Confirm

`AskUserQuestion`: "I'll run Codex as a second-opinion reviewer and iterate until clean. Proceed?"
Options: "Yes, run Codex review" (recommended) / "Skip Codex, go to user review" / "Cap iterations at N"

Skip for trivial plans (single-file, low-risk). Run for non-trivial (new module, schema/algorithm change).

### Loop

1. **Start**: invoke the `codex-plan-review` skill with the plan path.
2. **Parse trailing tag**: `APPROVED` -> Step 4. `NEEDS_REWORK` -> surface to user. `REQUEST_CHANGES` -> continue.
3. **Address findings critically** — quote each P1/P2, push back on incorrect ones, fix legitimate ones by editing the plan in place.
4. **Write implementer notes** (1-3 sentences): which findings you fixed, which you pushed back on and why, any user decisions that override existing docs or environment limitations that can't be resolved in the plan.
5. **Resume**: invoke `codex-plan-review` again with the same plan path, passing the notes — e.g. `<plan-path> Fixed X. Pushed back on Y because Z. User decided W.` The skill detects the stored review and switches to its resume prompt.
   -> back to step 2.
6. **Cap at 5 rounds** (or user-specified). Surface remaining findings and let user decide.

The notes are not optional: each Codex turn is a fresh run that only knows what the prompt carries, so without them Codex re-raises findings you already settled.

Surface Codex reviews verbatim. Keep edits scoped to findings. Reset (`codex-plan-review reset <plan-path>`) only if the review context is genuinely confused.

`codex-plan-review` needs the `codex-bridge` plugin. If it is not installed, either install it or skip Codex review and go straight to Step 4 — the loop is an accelerator, not a gate.

---

## Step 4: User Review & Validation

After Codex review converges (or is skipped), present a summary to the user including:

- **Feature**: [name]
- **Approach**: [1-2 sentences]
- **Files affected**: [count] files ([list key ones])
- **Estimated complexity**: [simple/moderate/complex]
- **Codex status**: [APPROVED / skipped / capped at N rounds with open findings]

Then **use the `AskUserQuestion` tool** to collect feedback:

- **Question**: "Please review the plan at `docs/1-plans/F_x.y.z_feature-name.plan.md`. How would you like to proceed?"
- **Options**: "Approved" (ready for implementation), "Request changes" (I have modifications), "Needs rework" (significant issues to address)

Handle feedback:

- **If "Request changes"**: Update the plan and re-present. Run another Codex pass if changes are substantive.
- **If "Needs rework"**: Discuss issues, rework the plan, and re-present.
- **If "Other" (custom input)**: Handle accordingly.
- **If "Approved"**: first persist the plan (below), then ask about implementation timing.

### Persist the Approved Plan

Once the plan is approved, create its feature branch immediately and push the plan doc — don't leave an approved plan sitting uncommitted on `main` even if implementation won't start right away.

1. `git status` to confirm a clean tree (stash/commit anything unrelated first — never carry someone else's uncommitted work onto a new branch).
2. `git checkout -b feat/[short-description]` (or `fix/[short-description]`), derived the same way `TRIP-2-implement` Step 0 derives it, so the two stay the same branch.
3. Commit **only** the plan file: `docs(plan): add <feature-name> implementation plan` (see the `commit` skill for message conventions — no `Co-Authored-By`), then `git push -u origin <branch>`.
4. Share the plan's GitHub blob link with the user (`https://github.com/<owner>/<repo>/blob/<branch>/docs/1-plans/F_x.y.z_<feature-name>.plan.md`) so it's reviewable/shareable before implementation begins.

Then **use the `AskUserQuestion` tool** to ask:
  - **Question**: "Plan approved and pushed on `<branch>`. Would you like to start implementation now?"
  - **Options**: "Yes, implement now" (proceed with `TRIP-2-implement` using this plan — it will continue on this same branch), "Not yet" (I'll implement later)

---

## IMPORTANT: No Code Implementation

**DO NOT write code snippets or implement anything during planning.**

This is a high-level planning phase only. Your plan should describe:

- WHAT needs to be done (features, changes, structures)
- WHERE changes will happen (files, modules, functions)
- WHY certain approaches are chosen (trade-offs, rationale)

But NOT:

- Actual code implementations
- Detailed algorithm code

Keep it architectural and descriptive. Code comes in the `TRIP-2-implement` phase.

## Guidance sections (from docs/TRIP.md § Guidance sections)

<!--
During Init, replace this section with project-specific guidance.
Examples:

For Web Frontend:
## For New UI Components
## For Service Layer Additions
## For Custom Hooks

For Embedded:
## For New Peripheral Drivers
## For New Communication Protocols

For CLI:
## For New Commands
## For Configuration Changes

For Backend:
## For New API Endpoints
## For Database Changes
-->
