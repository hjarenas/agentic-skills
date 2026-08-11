# Testing

## Framework

Python stdlib `unittest`. No pytest, no JS/TS test runner — nothing in this repo is a Node or
frontend project.

## What's tested today

Only `plugins/codex-bridge/tests/test_codex_run.py` (7 tests, all passing as of `TRIP-init`).
It loads `plugins/codex-bridge/scripts/codex-run.py` directly via `importlib.util.spec_from_file_location`
rather than importing it as a package — these are plugin scripts installed into a per-version
cache directory, not an installable Python package, so there is no `codex_run` module to `import`
normally. New tests for other scripts should follow the same pattern: a `tests/` directory next
to the script it covers, one test file per script, loaded via `importlib`.

## Commands

```bash
# Run all tests
python3 -m unittest discover -s plugins/codex-bridge/tests -p "test_*.py"

# Run a specific test
python3 -m unittest discover -s plugins/codex-bridge/tests -p "test_*.py" -k <pattern>
```

## Organization

- `plugins/codex-bridge/tests/test_codex_run.py` — covers `find_companion`, the logic that
  locates the installed `codex` plugin's companion cache across legacy and current layouts.

## Conventions observed

- `unittest.TestCase` subclasses, one class per function/concern under test
  (`FindCompanionTests`)
- Fixtures built with `tempfile` and `unittest.mock.patch`, not a separate fixtures directory
- Test names are full sentences describing the scenario
  (`test_current_layout_wins_over_newer_legacy_cache`)

## Coverage requirements

Not defined. This repo has no coverage tool configured and no threshold — invent neither. The
practical bar (see `docs/TRIP.md` § Test priorities) is: mechanically-checkable script logic
gets tests for its edge cases; `SKILL.md` prompt content does not, and is verified by invocation
instead.

## Scripts without tests yet

- `scripts/vendor-sync.py` — the 3-way merge logic (`clean`/`conflicted`/`gone` classification)
  is a good candidate; today it's verified by running `--check` against real upstream state.
- `plugins/trip-wiki/scripts/wiki_lint.py` — link resolution, frontmatter/body `links:`
  reconciliation, and size-limit checks are all pure functions on parsed page data and would
  test cleanly.
- `plugins/toolbox/skills/commit/scripts/check_message.py` — format and
  attribution validation; both are regex/string logic with clear expected inputs and outputs.

None of these are release blockers on their own — `docs/3-code-review/checklist.md` §5 asks for
a test or a documented reason whenever one of these scripts gains *new* logic, not for the
existing untested surface to be backfilled before that.
