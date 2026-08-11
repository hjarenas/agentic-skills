# Code Review Checklist

This file is the **single source of truth** for code-review criteria. Both human-driven reviews
via the `TRIP-review` skill and Codex-driven reviews via `codex-code-review` apply the criteria
below — referenced, not copied — so the two review surfaces cannot drift.

Tailored for `agentic-skills`: most changes here are `SKILL.md` prompt content, not application
code, so this checklist replaces the generic Error Handling/Security/Performance sections with
the things that actually break in this repo — stale pointers, cross-plugin references, and
version/README drift.

## Systematic Review Checklist

### 1. Functional Requirements

- [ ] The change matches what the plan (or the request, for unplanned work) actually asked for
- [ ] Edge cases and branch conditions in the skill's logic are covered, not just the happy path
- [ ] If a script's behavior changed, the change is grounded in a real run, not assumed

### 2. Skill / Prompt Quality

- [ ] Frontmatter is correct: `name` matches the directory, `description` has a front-loaded
  leading word and one trigger per branch, `disable-model-invocation` is a deliberate choice
  (not an accidental omission — see `writing-for-agents`'s guidance on this), `argument-hint`
  present when the skill takes arguments
- [ ] The description does not restate step logic the body can drift from underneath it (the
  2026-08-11 "ff-merge" finding is the concrete example of this going wrong)
- [ ] Reference material that only some branches need is disclosed behind a pointer, not
  inlined into every read
- [ ] Any negation/prohibition in the prompt is paired with the positive target, unless it's a
  hard guardrail that cannot be phrased positively

### 3. Architectural Compliance

- [ ] Consistent with the patterns documented in `docs/archi/` — if the change makes the wiki
  wrong, that's a finding, not something to note and move past
- [ ] A change to a plugin's skill set or responsibilities is reflected in its `docs/archi/`
  page, or flagged for a `wiki-ingest` pass

### 4. Distribution & Versioning

- [ ] The touched plugin's `plugins/<name>/.claude-plugin/plugin.json` version is bumped
  (semver) if this release includes it
- [ ] `README.md`'s plugin table is still accurate if a plugin's skill list changed
- [ ] A vendored `pocock-core` file was changed through `scripts/vendor-sync.py`, with
  `UPSTREAM.json` updated to match — never hand-edited in place

### 5. Script Correctness (Python utility scripts)

- [ ] No unjustified dynamic typing; imports organized, unused ones removed
- [ ] Subprocess calls and file paths are constructed safely — no shell injection, no trusting
  unsanitized input into a command line
- [ ] New logic in `codex-run.py`, `wiki_lint.py`, `check_message.py`, or `vendor-sync.py` has a
  test in that plugin's adjacent `tests/` directory, or a one-line reason it doesn't

### 6. Cross-Reference Integrity

- [ ] Every skill name, file path, and `${CLAUDE_PLUGIN_ROOT}`-relative reference the change
  touches or adds actually resolves — this repo has no compiler to catch a typo'd path
- [ ] `${CLAUDE_PLUGIN_ROOT}` is never used to reach across a plugin boundary; a cross-plugin
  call is always by skill name
- [ ] If the change touches `docs/archi/`, `python3 plugins/trip-wiki/scripts/wiki_lint.py`
  passes clean

---

## Issue Severity Classification

**Critical (Block Approval)**:

- A skill's frontmatter or body actively misleads (wrong description, stale claim contradicted
  by the skill's own behavior)
- A vendored file was hand-edited without going through `vendor-sync.py`, orphaning it from
  `UPSTREAM.json`
- A broken cross-plugin or cross-skill reference that will fail at invocation time

**Major (Require Immediate Fix)**:

- Plugin version not bumped for a change that should carry one
- README plugin table out of sync with actual skill contents
- Missing test for new Python script logic with no documented reason

**Minor (Should Fix)**:

- Inconsistent naming or formatting versus the rest of the plugin
- A pointer that could be sharper (weak trigger wording, restated identity)
- Missing or stale `docs/archi/` page content for a changed subsystem

**Suggestions (Nice to Have)**:

- A leading-word consolidation opportunity (a concept restated in full prose at multiple sites)
- Additional test coverage beyond what the change strictly requires

---

## Review Completion Criteria (Approval Gate)

Minimum for approval:

- [ ] All functional requirements implemented
- [ ] No critical or major issues remaining
- [ ] `python3 -m unittest discover -s plugins/codex-bridge/tests -p "test_*.py"` passes, if
  `codex-bridge` was touched
- [ ] `python3 plugins/trip-wiki/scripts/wiki_lint.py` passes clean, if `docs/archi/` was touched
- [ ] New Python script logic has test coverage, or a documented reason it doesn't
- [ ] Plugin version and README table updated where required
