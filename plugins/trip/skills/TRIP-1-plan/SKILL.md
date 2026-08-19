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

0. `docs/TRIP.md` must already exist — read it first, including `Agent routing`. If it is missing,
   stop immediately and tell the user to run `/TRIP-init` first (or `/TRIP-upgrade` for a project
   set up before TRIP became a plugin). Do not improvise a profile inline: a bootstrapped
   `docs/TRIP.md` skips `TRIP-init`'s review-checklist, changelog-table, and TESTING.md setup, and
   defaults decisions that `AskUserQuestion` should be asking about.
1. Dispatch `discovery` (read-only) with a concrete assignment, not just the feature request:

   ```
   Discovery assignment — <feature request>

   1. Read docs/archi/index.md in full, then the wiki pages covering the affected area,
      following [[links]] one hop. (Un-migrated projects: read docs/ARCHI.md in full instead.)
   2. Query code-review-graph: get_minimal_context(task="<feature summary>"), then
      semantic_search_nodes / query_graph (callers_of/imports_of) on the files this will
      likely touch.
   3. If the code-review-graph MCP tools are unavailable, say so explicitly in the report —
      do not silently fall back to file reads only; a missing tool is a coverage gap the
      planner and reviewer need to know about, not something to paper over.

   Report: wiki-vs-code drift, impacted files, real current callers/dependents, documented
   conventions, and open unknowns. End with `DISCOVERY_COMPLETE` or `DISCOVERY_PARTIAL`.
   ```

   Parse the trailing tag when present. During the cached-plugin transition, also accept a
   complete, coherent untagged evidence report; a missing tag alone does not make an arrived
   report incomplete. If no usable report arrives, follow `Waiting for a worker` in
   `agent-routing.md`; never wait unconditionally for a tag. Require the evidence report before
   dispatching `planner`.
2. Dispatch `planner` with the feature request, profile, and discovery report. The planner owns
   clarification proposals and every plan-file edit. Require `PLAN_COMPLETE` or `PLAN_PARTIAL`
   when the worker supports tags, but accept an untagged report from an older cached plugin
   install when the plan file shows the required post-dispatch delta and the report names what it
   changed. If no usable report arrives, follow `Waiting for a worker`; never wait
   unconditionally for a tag.

Apply that planner report rule to every later planner dispatch in this skill, including review
fixes and user-requested revisions.

The wiki documents intent; the graph reflects the code as it actually is. If they disagree (undocumented module, stale pattern), note the drift in the plan rather than silently trusting one over the other — and add a to-do to run `/wiki-ingest` after the work lands.

## Your Task

Plan the following feature: $ARGUMENTS

---

## Step 1: Discovery & Clarification (Interactive)

Engage in a discovery conversation to fully understand the user's intent before writing a plan.

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

Use the template and Quality Standards at `plan-template.md` in this skill's directory — copy its
structure into the new plan file, filling every bracketed placeholder.

---

## Step 3: Independent Second-Opinion Review

Before the user sees the plan, run the configured independent plan-review loop.

Before presenting the plan, validate the `Depends on:` graph across every `### Phase N` heading.
The `plan-reviewer`, or the planner as a self-check when independent review is skipped, must
confirm that at least one phase says `Depends on: none` and that the graph has no cycles. Check
cycles by tracing every phase's dependency chain back to a root; revisiting a phase already in
the current chain is a cycle. A missing root or any cycle is a blocking finding that must be fixed
before presentation, not an advisory note: either can leave `TRIP-2-implement` with unmerged
phases and an empty frontier, initially or after some root phases merge. The same reviewer (or
self-check) must also confirm the plan against `plan-template.md`'s Quality Standards explicitly
— cite where the plan falls short of Zero Ambiguity, File-Level Specificity, Architecture
Alignment, or Risk Assessment, not just that the required sections exist.

### Confirm

`AskUserQuestion`: "I'll run an independent second-opinion reviewer and iterate until clean. Proceed?"
Options: "Yes, run review" (recommended) / "Skip review, go to user review" / "Cap iterations at N"

Suppress this prompt when this skill runs as a child of `TRIP-auto`; the parent owns review
convergence and the interim checkpoint.

Skip for trivial plans (single-file, low-risk). Run for non-trivial (new module, schema/algorithm change).

### Loop

1. **Start**: dispatch the configured `plan-reviewer` with read-only access and the plan path. For `codex-bridge`, invoke `codex-plan-review` with explicit model/effort overrides.
2. **Parse trailing tag**: `APPROVED` -> Step 4. `NEEDS_REWORK` -> surface to user. `REQUEST_CHANGES` -> continue.
3. **Address findings** — dispatch `planner` to evaluate each P1/P2 and edit legitimate findings.
   It must document any pushback and end with `PLAN_COMPLETE` or `PLAN_PARTIAL` when supported.
4. **Collect planner notes** (1-3 sentences): parse that tag when present, but accept an untagged
   report from an older cached plugin install when the plan file shows the required post-dispatch
   delta and the report names what it changed. If no usable report arrives, follow
   `Waiting for a worker`; never wait unconditionally for the tag. Record which findings
   the planner fixed, which it pushed back on and why, plus user decisions or environment limitations.
5. **Resume**: dispatch `plan-reviewer` again with the same plan path and planner notes. For `codex-bridge`, invoke `codex-plan-review` with those notes and the configured overrides.
   -> back to step 2.
6. **Cap at 5 rounds** (or user-specified). Surface remaining findings and let user decide.

The notes are not optional: Codex is stateless, so without them it re-raises findings you already settled.

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

In a standalone run, **use the `AskUserQuestion` tool** to collect feedback:

- **Question**: "Please review the plan at `docs/1-plans/F_x.y.z_feature-name.plan.md`. How would you like to proceed?"
- **Options**: "Approved" (ready for implementation), "Request changes" (I have modifications), "Needs rework" (significant issues to address)

Suppress this prompt when this skill runs as a child of `TRIP-auto`; treat the plan as approved
once independent review has converged and proceed directly to *Persist the Approved Plan* below,
so the parent's interim checkpoint can name the feature worktree path.

Handle feedback:

- **If "Request changes"**: Dispatch `planner` to update the plan and re-present. Run another independent review if substantive.
- **If "Needs rework"**: Discuss issues, then dispatch `planner` to rework and re-present.
- **If "Other" (custom input)**: Handle accordingly.
- **If "Approved"**: first persist the plan (below), then ask about implementation timing.

### Persist the Approved Plan

Once the plan is approved, create its feature worktree immediately and push the plan doc — don't
leave an approved plan sitting uncommitted on `main` even if implementation won't start right
away.

1. From the primary working tree, dispatch `workspace-worker` to confirm a clean tree. If unrelated
   work exists, report it to the user; do not stash or commit it without authorization. The new
   worktree branches from this clean primary tree's main branch.
2. Have `workspace-worker` derive `<repo>` from the current repository directory's basename and
   compute one short collision-safe `<suffix>` (a hash or timestamp) for this flow. Have it run:
   ```bash
   git worktree add ../<repo>-<slug>-<suffix> -b feat/<slug>-<suffix> <main branch>
   # Use fix/<slug>-<suffix> for a fix.
   ```
   Compute the suffix once and retain the resulting worktree path and branch name for the whole
   flow; do not regenerate it in downstream steps.
3. From inside the new worktree, preserve the approved plan at the same repository-relative path,
   commit **only** that plan file, and push the new branch.
4. Share the plan's GitHub blob link with the user (`https://github.com/<owner>/<repo>/blob/<branch>/docs/1-plans/F_x.y.z_<feature-name>.plan.md`) so it's reviewable/shareable before implementation begins.

Every subsequent dispatch for this flow — `TRIP-2-implement`, `TRIP-3-release`, and every worker
they dispatch — must carry `../<repo>-<slug>-<suffix>` explicitly as its working directory. Do
not rely on the caller's current directory. Once cwd is threaded this way, `codex-run.py`'s
existing `Path.cwd()`-keyed `.codex-bridge/` state automatically isolates stored Codex reviews
and reports per worktree; rely on that behavior without adding another isolation mechanism.

In a standalone run, **use the `AskUserQuestion` tool** to ask:
  - Suppress this prompt when this skill runs as a child of `TRIP-auto`; return the approved plan
    and worktree details so the parent can continue autonomously.
  - **Question**: "Plan approved and pushed on `<branch>` in worktree `<worktree-path>`. Would you like to start implementation now?"
  - **Options**: "Yes, implement now" (proceed with `TRIP-2-implement` using this plan in that same worktree), "Not yet" (I'll implement later)

---

## Plans describe WHAT, WHERE, and WHY only

Features/changes/structures, the files/modules/functions they touch, and the trade-offs behind
the approach — architectural and descriptive. Implementation-level code belongs to
`TRIP-2-implement`.

## Guidance sections

Apply `docs/TRIP.md` § Guidance sections where relevant to this plan's area.
