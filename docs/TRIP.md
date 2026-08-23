# TRIP profile — agentic-skills

Written by `/TRIP-init` on 2026-08-11. Every TRIP skill reads this file. Edit it freely; it is
yours, and no plugin update will touch it.

## Project

- **Name**: agentic-skills
- **Type**: Library/SDK — a Claude Code **plugin marketplace**, not a conventional application.
  "The code" is mostly `SKILL.md` prompt content (Markdown), plus a thin Python utility layer
  where behavior must be mechanically reliable rather than model-interpreted
  (`scripts/vendor-sync.py`, `plugins/trip-wiki/scripts/wiki_lint.py`,
  `plugins/codex-bridge/scripts/codex-run.py`, `plugins/toolbox/skills/commit/scripts/check_message.py`).
- **Main branch**: main
- **Version file**: none, repo-wide. Each plugin carries its own semver in
  `plugins/<name>/.claude-plugin/plugin.json`, bumped independently when that plugin's files
  change. "Current version" below tracks this profile's own changelog/week bookkeeping only.
- **Current version**: 1.7.0
- **Version naming basis**: from v1.6.0 on, release artifacts (plan, CR, changelog, table row) are
  named by the version of the plugin the release changes — `trip` 1.6.0 — rather than by this
  profile's own counter, which is why the table jumps 0.2.0 → 1.6.0. The w1 artifacts were named
  by the profile counter (0.2.0) while `trip` itself was at 1.5.0.
- **Week anchor**: 2026-08-10
- **Architecture**: `docs/archi/` (wiki)

## Commands

| Purpose | Command |
| :--- | :--- |
| test:all | `python3 -m unittest discover -s plugins/codex-bridge/tests -p "test_*.py"` |
| test:specific | `python3 -m unittest discover -s plugins/codex-bridge/tests -p "test_*.py" -k <pattern>` |

No lint, typecheck, or build tooling is configured — there is nothing to compile, and the
"source" is prompt content a linter cannot meaningfully check. `codex-bridge` is the only plugin
with a real Python test suite today; other plugins' scripts (`vendor-sync.py`, `wiki_lint.py`,
`check_message.py`) have none yet.

## Agent routing

Invocation arguments override this table for the current run. Blank model or effort means the
harness default.

| Role | Harness | Model | Effort |
| :--- | :--- | :--- | :--- |
| discovery | subagent |  |  |
| planner | subagent |  |  |
| plan-reviewer | codex-bridge |  |  |
| implementer | codex-bridge |  |  |
| batch-reviewer | subagent |  |  |
| fixer | subagent |  |  |
| test-worker | subagent |  |  |
| code-reviewer | codex-bridge |  |  |
| workspace-worker | subagent |  |  |
| release-worker | subagent |  |  |
| release-verifier | subagent |  |  |

## Integration checks

None. There is no integration/E2E tooling — a skill change is verified by actually invoking the
skill in a live Claude Code session, not by an automated harness. Python script changes are
covered by unit tests only where a `tests/` directory already exists next to the script
(currently `plugins/codex-bridge/tests/` only).

## Plan considerations

- **Frontmatter contract**: every `SKILL.md` needs a correct `name`, a `description` with a
  front-loaded leading word and one trigger per branch (see `writing-for-agents` in
  `pocock-core`), a deliberate `disable-model-invocation` choice, and an `argument-hint` when
  the skill takes arguments.
- **Cross-plugin references**: `${CLAUDE_PLUGIN_ROOT}` never resolves across plugin boundaries —
  invoke another plugin's skill by name, never by constructing a path through it.
- **Single source of truth**: a skill's `description` must not restate step logic the body can
  later change without — that drift already happened once (`TRIP-3-release`'s description said
  "ff-merge" long after the release flow moved to a pull request; fixed 2026-08-11).
- **Plugin version bump**: any change under `plugins/<name>/` bumps that plugin's
  `plugin.json` version and, if its skill list changed, `README.md`'s plugin table.
- **Vendored content** (`pocock-core`): route every change through `scripts/vendor-sync.py`;
  never hand-edit a vendored file without updating `UPSTREAM.json`'s pinned commit and hashes,
  or the next sync either overwrites the edit or falsely reports it as drift.
- **No AI commit attribution** — already enforced by `toolbox`'s `commit` skill and its
  `commit-msg` hook; nothing extra to do per plan.

## Guidance sections

### For skill changes (`SKILL.md` edits)

Frontmatter correctness (`name`/`description`/`disable-model-invocation`/`argument-hint`),
description quality (leading word, one trigger per branch, no restated body identity),
cross-references to other skills/files still resolve, and the model-invocation choice matches
the skill's actual blast radius (autonomy-maximizing or side-effecting skills stay user-invoked).

### For plugin-version releases

Which `plugin.json`(s) to bump and by how much (semver), whether `README.md`'s plugin table
needs a sync, and whether the change is architecturally significant enough to warrant a
`wiki-ingest` pass.

### For vendored `pocock-core` changes

Route through `scripts/vendor-sync.py`. A file upstream merely edited merges cleanly; a file
upstream **renamed or restructured** is reported as "removed or renamed" and needs manual
reconciliation — update `UPSTREAM.json`'s `skills` and `files` entries to match.

### For Python script changes (`scripts/*.py`, `plugins/*/scripts/*.py`)

Add or update tests in the adjacent `tests/` directory if one exists. No lint/typecheck harness
exists yet, so careful review substitutes for both.

## Test structure

Only `plugins/codex-bridge/tests/` exists today: stdlib `unittest`, one file
(`test_codex_run.py`), which loads the sibling `scripts/codex-run.py` via `importlib.util`
rather than a package import — these are plugin scripts, not an installable package. New Python
script tests should follow the same plugin-adjacent `tests/` pattern.

## Test priorities

The only mechanically-testable surface is the Python utility scripts: `codex-run.py`'s companion
cache discovery logic, `wiki_lint.py`'s link/frontmatter/size checks, `check_message.py`'s
commit-message validation, and `vendor-sync.py`'s 3-way merge logic. Prioritize edge cases and
regressions there. `SKILL.md` content itself is not unit-testable — verify a skill by invoking
it in a live session.

## Tutorials

- **Enabled**: yes
- **Level**: intermediate
- **Focus**: Claude Code plugin/skill mechanics; the tooling this repo builds (TRIP, the
  architecture wiki, codex-bridge internals)
- **Style**: concise

Revisit whether this is still worth generating around 2026-09-11 — enabled on a trial basis at
`TRIP-init` time; a scheduled reminder was set separately to prompt that reassessment.

## Custom plan sections

None.
