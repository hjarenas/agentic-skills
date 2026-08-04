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

## Operating model

Read and obey [the agent routing contract](../../references/agent-routing.md). Parse routing
overrides from `$ARGUMENTS`, then treat the remainder as the plan or feature. You are a pure
orchestrator. There are no trivial-change or small-fix exceptions.

---

## Step 0: Create a Branch (Pre-Implementation)

**Always** work on a dedicated branch. Dispatch `workspace-worker` for every branch operation.

`TRIP-1-plan` now creates and pushes this branch (with the plan doc as its first commit) as soon as the plan is approved, so the common case is that it **already exists**:

- Check first: does `docs/1-plans/F_x.y.z_<feature-name>.plan.md` already exist committed on a `feat/`/`fix/` branch (locally or on `origin`)? If so, `git checkout` that branch (or `git fetch` + checkout if it's only on `origin`) and continue on it — do **not** create a new one.
- Only if no such branch exists (e.g. the plan was written directly without going through `TRIP-1-plan`'s persist step, or implementation is resuming from an unpushed local plan file) create one fresh:
  ```bash
  git checkout -b feat/[short-description]   # or fix/[short-description]
  ```
  Derive the short description from the plan/feature name — matching what `TRIP-1-plan` would have derived, so the two never diverge.

If already on the correct dedicated branch for this work (e.g., resuming a session), continue on it either way.

---

## Implementation Phase — Delegate to the configured workers

Dispatch all implementation to the configured `implementer`. For `codex-bridge`, use the
`codex-implement` skill with explicit model/effort overrides. Other harnesses receive the same
batch scope and completion contract.

Delegation is **batched**: the implementer handles a few checkboxes per turn, an independent
batch reviewer checks them, and a fixer handles corrections. Carry explicit notes between turns.

### 1. Read the plan and decide the batches

Read the plan fully and split its to-dos into batches. You are the judge of batch size:

- A batch is the **smallest set of checkboxes that leaves the tree green** (compiles, lints). Never split an interface from its implementation and wiring.
- Target a reviewable diff — roughly ≤300 changed lines per batch. A checkbox that alone exceeds this becomes its own batch.
- Size by risk: novel, architectural, or security-critical work → small batches (down to one checkbox). Mechanical, repetitive work → larger batches.
- Never span phase boundaries.
- **One-shot escape hatch**: a low-risk plan (or phase) of ≤3-4 checkboxes is delegated whole — no batching ceremony.
- **Filter out blocked items**: checkboxes needing human input, dashboard access, credentials, or
  expanded authority must be raised with the user; the orchestrator coordinates but does not execute them.

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

After each implementer report, before requesting the next batch:

1. **Prepare delta inputs**: have `workspace-worker` capture `git status -s && git diff`; give
   that raw delta to `batch-reviewer`, which also runs graph change/flow analysis and checks the
   plan, documented patterns, and project conventions.
2. Dispatch `batch-reviewer` read-only for the raw delta and graph impact. Require findings with file/line evidence and a verdict.
3. If findings exist, dispatch `fixer`; then dispatch `batch-reviewer` again to verify the corrections. Never let the implementer approve its own batch.
4. Dispatch `test-worker` for the lint and typecheck/build micro-gate. Route failures to `fixer`, then rerun `test-worker`.
5. Dispatch a worker to stage the reviewed batch with `git add -A`. No commits — history stays clean for release.
6. Have `batch-reviewer` verify completed plan checkboxes against the diff; have `planner` update missed checkbox state.

**Adapt as you go**: clean batch → grow the next one; heavy corrections → shrink the next one and spell out the fix pattern in the notes. If Codex ignores notes or repeats corrected mistakes late in a long session, reset the thread at the next batch boundary — the plan file plus a summary note rebuilds context.

### 4. Final pass

After the last batch, dispatch `batch-reviewer` for the **full feature diff** and full-feature
blast radius. Route corrections to `fixer`, then re-review until clean.

The full testing gate and independent code review run **once**, after the final pass — never per batch.

---

## Testing Gate

After implementation, before the code-review loop. Dispatch the entire gate to `test-worker`.
Route failures to `fixer` and rerun the gate. Any failure blocks review.

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

If the change adds new logic, instruct `test-worker` to write its tests **now**, guided by the
plan's **Test Impact** section and `TRIP-test`. If no new logic was added, skip this step.

**Hard-to-cover code policy:**

- Test **observable behavior** (inputs → outputs/persisted effects), never internal wiring.
- **Mock-pain tripwire**: if the mock setup grows longer than the test's assertions, stop fighting it — check the project's testing guide for a seam recipe; if none applies, skip the *deep unit* test and add one line to `docs/4-unit-tests/COVERAGE-DEBT.md` (`path | why hard | escape plan`).
- **Critical-path floor**: behavior touching auth, deletion, persistence, cost, or external request shape must keep at least one behavioral test or manual integration check — coverage debt may defer internal-path depth, never safety-critical behavior.
- Never hide untested code (no coverage-ignore comments, no config exclusions, no lowering coverage gates). Legacy modules outside the change scope are not a feature blocker — but record newly encountered risky gaps in the ledger.

### 5. Build the summary

Format: `lint: clean | typecheck: clean | tests: N passed (M new)`

Fix failures before starting the loop.

---

## Independent Code Review

Always dispatch the configured `code-reviewer` after the testing gate passes. It must be
independent from the implementer, batch reviewer, fixer, and test worker.

### Loop

1. **Start**: dispatch `code-reviewer` with the plan path and testing-gate summary. For
   `codex-bridge`, invoke `codex-code-review` with explicit model/effort overrides:
   ```
   codex-code-review <plan-path> $GATE_SUMMARY
   ```
   `$GATE_SUMMARY` is the testing-gate summary (`lint | typecheck | tests`). For unplanned work (no `F_*.plan.md`), pass a free-form label instead of a plan path.

2. **Parse trailing tag**: `APPROVED` -> synthesize. `NEEDS_REWORK` -> surface to user. `REQUEST_CHANGES` -> continue.

3. **Address findings** — dispatch `fixer` with each evidenced finding. Send disputed findings
   to a fresh `code-reviewer` assignment with the rationale; the orchestrator does not adjudicate
   the code itself. Critical/Major findings block approval.

4. **Build worker notes** from the fixer and reviewer reports: fixes made, disputed findings and
   why, plus user decisions or environment limitations the reviewer should not re-flag.

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

Surface reviews verbatim. Keep fixer edits scoped. If a reviewer repeats a finding, dispatch a
fresh `batch-reviewer` to determine whether the fix addressed an adjacent concern or the notes
were incomplete. The testing gate must pass before APPROVED.

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
