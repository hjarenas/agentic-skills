---
name: TRIP-test
description: Write/run tests following project standards (deep test authoring)
disable-model-invocation: true
argument-hint: "component or feature to test"
---

# Testing Mode

You are now in **testing mode** for **this project**.

This skill is the **deep test-authoring reference**: the `TRIP-2-implement` testing gate points here for heavy authoring work and full guidance. Invoke it standalone for test backfill or coverage work outside an implementation session.

## Prerequisites - Read First

Before testing, you MUST read:

1. `docs/archi/index.md` and the pages covering the code under test - understand system architecture. (Projects that have not run `/wiki-migrate` still have a monolithic `docs/ARCHI.md`; read that instead.)
2. @docs/4-unit-tests/TESTING.md - Testing guidelines

Then check current coverage with the code-review-graph MCP tools: `query_graph_tool` with pattern `tests_for` on the target function/module, so you know what's already covered before writing anything new.

## Your Task

Test: $ARGUMENTS

---

## Testing Guidelines

### Scope

- Only run tests for relevant files that changed (not the whole project)
- Focus on the new feature/fix/refactor

### Commands

```bash
# Commands come from docs/TRIP.md § Commands — read it first.

# Run all tests
<test:all — docs/TRIP.md § Commands>

# Run specific test
<test:specific — docs/TRIP.md § Commands>

# With coverage
<test:coverage — docs/TRIP.md § Commands>
```

### Test Structure

Test locations and naming conventions: see docs/TRIP.md § Test structure.

### Testing Priorities

<!-- Project-specific testing priorities live in docs/TRIP.md § Test priorities. -->

**Unit Tests**:

- Core logic functions
- Utility functions
- Individual modules/components

**Integration Tests**:

- Module interactions
- External service integration
- End-to-end flows

**What to Test**:

- Happy path scenarios
- Error states and error handling
- Edge cases (null, empty, boundary values)
- Invalid inputs

---

## Hard-to-Test Code

Seam ladder, cheapest first: **exported pure helper → injectable client/adapter → module mock → integration/emulator test**. Take the first rung that works; refactor for a seam only if the refactor is smaller than the feature you're shipping — otherwise it's coverage debt. Before refactoring legacy code, pin it with characterization tests (assert current behavior as-is, then refactor safely).

Uncovered risky paths: one line each in `docs/4-unit-tests/COVERAGE-DEBT.md` (`path | why hard | escape plan`). Delete a ledger line in the same change that gives its path meaningful coverage.

---

## Post-Testing Summary

After completing tests, create a summary file:

**File**: `docs/4-unit-tests/wa_vx.y.z_test.md`
(a = project week, x.y.z = version)

**Content**:

```markdown
# Test Summary - Week a, V. x.y.z

## What Was Tested

[List of tested components/functions]

## Test Results

- Total tests: X
- Passed: X
- Failed: X
- Coverage: X%

## Key Findings

[Any issues discovered, edge cases found, etc.]

## Notes

[Additional context or recommendations]
```
