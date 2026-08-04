---
name: TRIP-1-plan
description: Plan a new feature following project standards
argument-hint: "describe the feature you want to build"
---

# Planning Mode

You are now in **planning mode** for **this project**.

## Operating model

Read and obey [the agent routing contract](../../references/agent-routing.md). Parse routing
overrides from `$ARGUMENTS`, then treat the remainder as the feature request. You are the
orchestrator: all discovery, plan writing, and review work must be performed by workers.

## Prerequisites - Read First

Before dispatching planning workers:

0. Read `docs/TRIP.md`, including `Agent routing`. If it is missing, run `/TRIP-init` first (or `/TRIP-upgrade`).
1. Dispatch `discovery` to read the relevant wiki pages and query the code-review graph. Require an evidence report including drift, impacted files, callers, conventions, and unknowns.
2. Dispatch `planner` with the feature request, profile, and discovery report. The planner owns clarification proposals and every plan-file edit.

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

Once understanding is confirmed, instruct the `planner` worker to create the plan document.

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

## Step 3: Independent Second-Opinion Review

Before the user sees the plan, run the configured independent plan-review loop.

### Confirm

`AskUserQuestion`: "I'll run an independent second-opinion reviewer and iterate until clean. Proceed?"
Options: "Yes, run review" (recommended) / "Skip review, go to user review" / "Cap iterations at N"

Skip for trivial plans (single-file, low-risk). Run for non-trivial (new module, schema/algorithm change).

### Loop

1. **Start**: dispatch the configured `plan-reviewer` with read-only access and the plan path. For `codex-bridge`, invoke `codex-plan-review` with explicit model/effort overrides.
2. **Parse trailing tag**: `APPROVED` -> Step 4. `NEEDS_REWORK` -> surface to user. `REQUEST_CHANGES` -> continue.
3. **Address findings** — dispatch `planner` to evaluate each P1/P2 and edit legitimate findings. It must document any pushback.
4. **Collect planner notes** (1-3 sentences): which findings the planner fixed, which it pushed
   back on and why, plus user decisions or environment limitations.
5. **Resume**: dispatch `plan-reviewer` again with the same plan path and planner notes. For `codex-bridge`, invoke `codex-plan-review` with those notes and the configured overrides.
   -> back to step 2.
6. **Cap at 5 rounds** (or user-specified). Surface remaining findings and let user decide.

The notes are not optional: each Codex turn is a fresh run that only knows what the prompt carries, so without them Codex re-raises findings you already settled.

Surface worker reviews verbatim. Keep planner edits scoped to findings. Reset persistent reviewer
state only if genuinely confused.

If the selected harness is unavailable, ask the user to choose an installed harness. Do not
silently replace or skip a configured reviewer.

---

## Step 4: User Review & Validation

After independent review converges (or is explicitly skipped), present a summary including:

- **Feature**: [name]
- **Approach**: [1-2 sentences]
- **Files affected**: [count] files ([list key ones])
- **Estimated complexity**: [simple/moderate/complex]
- **Review status**: [harness/model, APPROVED / skipped / capped with open findings]

Then **use the `AskUserQuestion` tool** to collect feedback:

- **Question**: "Please review the plan at `docs/1-plans/F_x.y.z_feature-name.plan.md`. How would you like to proceed?"
- **Options**: "Approved" (ready for implementation), "Request changes" (I have modifications), "Needs rework" (significant issues to address)

Handle feedback:

- **If "Request changes"**: Dispatch `planner` to update the plan and re-present. Run another independent review if substantive.
- **If "Needs rework"**: Discuss issues, then dispatch `planner` to rework and re-present.
- **If "Other" (custom input)**: Handle accordingly.
- **If "Approved"**: first persist the plan (below), then ask about implementation timing.

### Persist the Approved Plan

Once the plan is approved, create its feature branch immediately and push the plan doc — don't leave an approved plan sitting uncommitted on `main` even if implementation won't start right away.

1. Dispatch `workspace-worker` to confirm a clean tree. If unrelated work exists, report it to the user; do not stash or commit it without authorization.
2. Have `workspace-worker` create `feat/[short-description]` (or `fix/[short-description]`).
3. Have `workspace-worker` commit **only** the plan file and push the branch.
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
