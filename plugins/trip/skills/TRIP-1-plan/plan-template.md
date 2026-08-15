Template for the plan document the `planner` worker creates in Step 2 — copy this structure into
`docs/1-plans/F_[version]_[feature-name].plan.md`, filling in every bracketed placeholder.

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

Depends on: none

- [ ] Task description
- [ ] Another task

### Phase 2: [Phase Name] (if applicable)

Depends on: Phase 1

- [ ] Task description
- [ ] Another task

**Note**: For simple plans, a single phase with `Depends on: none` is sufficient. For multiple
phases, judge dependencies by whether they touch disjoint files or subsystems: phases with
`Depends on: none` may run concurrently during `TRIP-2-implement`; name another phase only when
its files must genuinely exist first. Getting this wrong is recoverable but causes a merge-conflict
pause, so judge conservatively when unsure. Examples: `Depends on: none`; `Depends on: Phase 1`.

**Note**: If a phase introduces a new end-to-end capability or flow (a new principal, a new
integration path, anything with an outside observer), make proving that flow reachable — one real
test or manual check that a real caller can complete it, not a unit test of its parts — the
**first** checklist item of that phase, not the last. A suite that stays green while the flow
itself is unusable is a common and expensive failure mode; ordering the reachability check first
catches it on day one of the phase instead of after every other item is already built on top of
the broken assumption.

**Note**: Do NOT write test code during planning — the Test Impact section above only names what the TRIP-2 testing gate will run and author.

**Note**: Once implementation is underway, a decision that changes what an earlier checklist
bullet says must be applied by editing that bullet in place and marking it superseded — never by
appending the correction elsewhere in the document. This applies during planning too: if review
or a later phase's context changes an earlier bullet's meaning before the plan is even approved,
fix it in place.
```

## Quality Standards

- **Zero Ambiguity**: Every step must be clear and actionable
- **File-Level Specificity**: List exact files and functions to modify
- **Architecture Alignment**: Must conform to the patterns documented in `docs/archi/`, cross-checked against the graph's current callers/dependents where relevant
- **Risk Assessment**: Highlight potential failure points
