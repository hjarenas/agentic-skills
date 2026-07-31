---
name: TRIP-2-implement
description: Implement a feature following TRIP plan
argument-hint: "plan file or feature to implement"
---

# Implementation Mode

You are now in **implementation mode** for **this project**.

## Prerequisites - Read First

Before implementing:

0. Read `docs/TRIP.md` — this project's TRIP profile: name, type, main branch, version file, week anchor, the lint/typecheck/test commands, and the project-specific sections this skill refers to. It is written by `TRIP-init`. If it is missing, run `/TRIP-init` first (or, for a project set up before TRIP became a plugin, `/TRIP-upgrade`).
1. Read `docs/archi/index.md` in full, then open the wiki pages covering the area the plan touches and follow their `[[links]]` one hop — documented architecture, rationale, and conventions. (Un-migrated projects: read `docs/ARCHI.md` in full instead.)
2. Query the code-review-graph MCP tools for the plan's target area: `get_minimal_context(task="<feature summary>")`, then `semantic_search_nodes`/`query_graph` (`callers_of`/`imports_of`) on the files the plan will touch, so you know the real current callers/dependents before changing them. Use `detail_level="minimal"`.

## Your Task

Implement: $ARGUMENTS

---

## Step 0: Create a Branch (Pre-Implementation)

**Always** work on a dedicated branch — no need to ask. `TRIP-3-release` merges it back into the main branch with fast-forward, keeping a single clean linear history.

`TRIP-1-plan` now creates and pushes this branch (with the plan doc as its first commit) as soon as the plan is approved, so the common case is that it **already exists**:

- Check first: does `docs/1-plans/F_x.y.z_<feature-name>.plan.md` already exist committed on a `feat/`/`fix/` branch (locally or on `origin`)? If so, `git checkout` that branch (or `git fetch` + checkout if it's only on `origin`) and continue on it — do **not** create a new one.
- Only if no such branch exists (e.g. the plan was written directly without going through `TRIP-1-plan`'s persist step, or implementation is resuming from an unpushed local plan file) create one fresh:
  ```bash
  git checkout -b feat/[short-description]   # or fix/[short-description]
  ```
  Derive the short description from the plan/feature name — matching what `TRIP-1-plan` would have derived, so the two never diverge.

If already on the correct dedicated branch for this work (e.g., resuming a session), continue on it either way.

---

## Implementation Phase — Delegate to Codex

You do NOT write the implementation yourself — delegate it to Codex via the `codex-implement` skill. (Exception: trivial unplanned changes of a few lines may be done directly.)

Delegation is **batched**: Codex implements a few of the plan's checkboxes per turn, you review and fix each batch, then request the next one with your corrections attached. Same persistent thread throughout — context and conventions compound across turns.

### 1. Read the plan and decide the batches

Read the plan fully and split its to-dos into batches. You are the judge of batch size:

- A batch is the **smallest set of checkboxes that leaves the tree green** (compiles, lints). Never split an interface from its implementation and wiring.
- Target a reviewable diff — roughly ≤300 changed lines per batch. A checkbox that alone exceeds this becomes its own batch.
- Size by risk: novel, architectural, or security-critical work → small batches (down to one checkbox). Mechanical, repetitive work → larger batches.
- Never span phase boundaries.
- **One-shot escape hatch**: a low-risk plan (or phase) of ≤3-4 checkboxes is delegated whole — no batching ceremony.
- **Filter out non-Codex items**: checkboxes needing human input, dashboard/console access, credentials, or ops actions are yours — resolve them with the user before or between batches, never delegate them.

### 2. Delegate batch by batch

**Start** the session with the first batch by invoking the `codex-implement` skill:

```
codex-implement <plan-path> Implement only: <batch-1 checkboxes>
```

(Omit the instructions to one-shot a small plan.)

**Each next batch continues the same session**, carrying your review corrections as notes:

```
codex-implement <plan-path> Notes: <what you fixed after the last batch and why; conventions to
apply from now on>. Now implement: <next batch checkboxes>
```

The skill resumes the workspace's last Codex thread for the next batch. That is only correct if
nothing else ran Codex in between — if you used `codex-ask`, `/codex:review` or
`/codex:adversarial-review` between batches, say so, and the skill will start fresh and rely on
the notes instead.

**Parse the trailing tag** of each report:
- `IMPLEMENTATION_COMPLETE` → review the batch (below).
- `IMPLEMENTATION_PARTIAL` → read the report; resume with instructions for the remainder, or finish small leftovers yourself during the batch review.

### 3. Review each batch (delta review)

After each Codex report, before requesting the next batch:

1. **Review the delta**: `git status -s && git diff` for the raw change, plus `detect_changes_tool` (risk-scored analysis) and `get_affected_flows_tool` (impacted execution paths) from code-review-graph — worktree vs index shows just this batch, since previous batches are staged (step 4). Check it against the plan, the patterns documented in the wiki pages you read in Prerequisites, and project conventions (DRY, KISS, comment discipline, error-handling and naming conventions).
2. **Fix problems directly yourself** — no back-and-forth with Codex over fixes. What you fixed and why becomes the `--notes` of the next resume.
3. **Micro-gate**: run the lint and typecheck/build commands from the Testing Gate (fast checks only — tests wait for the gate itself). Fix failures now.
4. **Checkpoint**: `git add -A` — stage the reviewed batch so the next delta review starts clean. No commits — history stays clean for release.
5. Verify the plan checkboxes Codex ticked match what the diff actually contains; cross any it completed but missed.

**Adapt as you go**: clean batch → grow the next one; heavy corrections → shrink the next one and spell out the fix pattern in the notes. If Codex ignores notes or repeats corrected mistakes late in a long session, reset the thread at the next batch boundary — the plan file plus a summary note rebuilds context.

### 4. Final pass

After the last batch, read the **full feature diff** once (`git diff HEAD`), and run `get_impact_radius_tool`/`get_affected_flows_tool` on the changed modules for the full-feature blast radius. Batch reviews catch local issues; this pass catches cross-batch drift — duplicated helpers, divergent naming, dead code left by course corrections. Fix directly.

The testing gate and Codex code review run **once**, after the final pass — never per batch. Proceed to the testing gate once you consider the implementation good for review.

---

## Testing Gate

After implementation, before the Codex review loop. Any failure here blocks the loop from starting.

### 1. Lint, type-check & build

```bash
# Commands come from docs/TRIP.md § Commands — read it first.
<lint command — docs/TRIP.md § Commands> 2>&1 | tee /tmp/_trip2-lint.txt
<typecheck command — docs/TRIP.md § Commands> 2>&1 | tee /tmp/_trip2-typecheck.txt
```

### 2. Run affected unit tests

```bash
<test command — docs/TRIP.md § Commands> <pattern-for-affected-files>
```

Only the files/areas the change touched — never the full suite by default.

### 3. Integration impact check

<!-- The project's integration/E2E impact rules live in docs/TRIP.md § Integration checks. -->

If the change modifies an externally observable contract (API shape, UI selectors, auth behavior), exercise it with the project's integration/E2E tooling. Docs-only changes skip this.

If the change touches a cloud or infrastructure boundary that local tests cannot
exercise (IaC resources, IAM, networking, managed-service integrations), verify it
against the real environment before this gate can pass — a green `terraform validate`
and a green unit suite do not mean the deployed behaviour is correct. Record the
project's rule for this in `docs/TRIP.md` § Integration checks, along with any
project-specific skill that performs the verification.

### 4. Author missing tests

If the change adds new logic, write its tests **now**, guided by the plan's **Test Impact** section and the project's testing guide (see `TRIP-test`). If no new logic was added, skip this step.

**Hard-to-cover code policy:**

- Test **observable behavior** (inputs → outputs/persisted effects), never internal wiring.
- **Mock-pain tripwire**: if the mock setup grows longer than the test's assertions, stop fighting it — check the project's testing guide for a seam recipe; if none applies, skip the *deep unit* test and add one line to `docs/4-unit-tests/COVERAGE-DEBT.md` (`path | why hard | escape plan`).
- **Critical-path floor**: behavior touching auth, deletion, persistence, cost, or external request shape must keep at least one behavioral test or manual integration check — coverage debt may defer internal-path depth, never safety-critical behavior.
- Never hide untested code (no coverage-ignore comments, no config exclusions, no lowering coverage gates). Legacy modules outside the change scope are not a feature blocker — but record newly encountered risky gaps in the ledger.

### 5. Build the summary

Format: `lint: clean | typecheck: clean | tests: N passed (M new)`

Fix failures before starting the loop.

---

## Codex Code Review

Always run the Codex code review after the testing gate passes — no confirmation needed.

### Loop

1. **Start**: invoke the `codex-code-review` skill with the plan path and the testing-gate summary:
   ```
   codex-code-review <plan-path> $GATE_SUMMARY
   ```
   `$GATE_SUMMARY` is the testing-gate summary (`lint | typecheck | tests`). For unplanned work (no `F_*.plan.md`), pass a free-form label instead of a plan path.

2. **Parse trailing tag**: `APPROVED` -> synthesize. `NEEDS_REWORK` -> surface to user. `REQUEST_CHANGES` -> continue.

3. **Address findings** — quote each with `file:line`, read the actual code, fix legitimate ones, push back on incorrect ones. Critical/Major block approval; Minor/Suggestion are case-by-case.

4. **Write implementer notes** (1-3 sentences): which findings you fixed, which you pushed back on and why, any user decisions or environment limitations Codex should stop re-flagging.

5. **Resume** (re-run the testing gate first — lint, typecheck, affected tests — and build a fresh summary): invoke `codex-code-review` again with the same target, passing the notes and the fresh gate summary. The skill detects the stored review and switches to its resume prompt.
   Loop to step 2.

6. **Cap at 5 rounds** (or user-specified). Surface remaining findings.

**For a risky change**, run `/codex:adversarial-review` once alongside this loop. It attacks the
design rather than the implementation — trust boundaries, rollback safety, race conditions — which
this loop does not do. Treat its findings as input to step 3, not as a separate gate.

### Synthesize

Skip if the loop converged on turn 1 — the stored review already holds everything.

Each turn stores only that turn's review. After multi-round convergence, produce a consolidated one by invoking `codex-code-review` with its synthesize step, passing a round-by-round summary and today's date (see that skill's "After Convergence" section).

Outputs `PROMOTION_READY` sentinel. `<x.y.z>` Version placeholder left unfilled (resolved during `TRIP-3-release`).

Edge cases:
- **Capped without APPROVED**: still synthesize; Codex notes open findings.
- **User skipped Codex**: no synthesis. The CR is written manually during `TRIP-3-release`: "Code review skipped — trivial change."

### Operating Notes

Surface reviews verbatim. Keep edits scoped. If Codex repeats a finding, re-read carefully — you likely addressed an adjacent concern, or you omitted the notes that told it the matter was settled. Reset only if the review context is confused. The testing gate (lint, typecheck, affected tests) must pass before APPROVED.

Every Codex turn is a fresh run whose only memory is what the prompt carries, so the implementer notes in step 4 are load-bearing. Skipping them is the single most common cause of a loop that will not converge.

---

## Handoff to Release

After Codex converges (or is skipped):

- Cross the corresponding checkboxes in the plan todo list (if any)
- Then **use the `AskUserQuestion` tool** to ask:
  - **Question**: "Is the implementation complete?"
  - **Options**: "Yes, everything is complete" (proceed to release), "No, there are remaining items" (continue working)

**If "Yes"**: proceed directly into the release — invoke the `TRIP-3-release` skill and follow it in this session, passing the same plan path (or feature label). The release skill owns everything from version bump to the fast-forward merge and push.

**If "No"**: continue working, then repeat the sequence: testing gate → Codex review → this question.
