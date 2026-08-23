# Code Review: Reachable TRIP-upgrade Standalone Migrations

**Review Date**: 2026-08-24
**Version**: 1.7.1
**Files Reviewed** (full change set, 9 paths; the independent `code-reviewer`'s two rounds
re-examined only `TRIP-upgrade/SKILL.md`, marked *. The unmarked paths were not examined by
`code-reviewer`: seven are release artifacts, and `TRIP-3-release/SKILL.md` is a late change added
after both review rounds closed — all eight are covered by `release-verifier` instead):

- `plugins/trip/skills/TRIP-upgrade/SKILL.md` *
- `plugins/trip/skills/TRIP-3-release/SKILL.md`
- `plugins/trip/.claude-plugin/plugin.json`
- `docs/TRIP.md`
- `docs/archi/pages/trip-plugin.md`
- `docs/archi/log/v1.7.1.md`
- `docs/2-changelog/w3_v1.7.1.md`
- `docs/2-changelog/changelog_table.md`
- `docs/3-code-review/CR_w3_v1.7.1.md`

**Plan**: no plan — patch fixing a defect in 1.7.0

---

## Executive Summary

`trip` 1.7.0 added two standalone `TRIP-upgrade` migrations — the worktree-bootstrap profile
subsection and the `git worktree` permission allowlist — but neither was reachable by the projects
that needed them, because Phase 0's path table stopped an already-routed project with "already
current" and the profile-only routing path ended by skipping Phases 1-6. This patch splits Phase 0
into two independent decisions, a structural path and a set of standalone migrations, so each
migration runs whenever its own condition holds. Reviewed by an independent `code-reviewer` over
two rounds: 1 Major, 2 Minor, 2 Suggestions, all addressed. **APPROVED**

---

## Changes Overview

One file changes, `plugins/trip/skills/TRIP-upgrade/SKILL.md` (~31 insertions / 11 deletions), all
prose; no scripts and no other plugin. Phase 0 now selects one **structural path** from a
four-row table and separately runs each **standalone migration** whose condition holds, on the
legacy, routing and "no structural work" paths alike. The "already current" no-op exit survives
but now additionally requires both standalone conditions to be satisfied. The profile-only routing
migration hands off to the standalone migrations before skipping Phases 1-6, and Phase 6 gained
the same hand-off for the legacy path. The frontmatter `description` now names both migrations,
which is what makes them discoverable.

A second, smaller change landed late in the release:
`plugins/trip/skills/TRIP-3-release/SKILL.md` (8 insertions / 2 deletions), also prose. Step 3.3
now says where the CR's **Files Reviewed** list comes from — derive it from the real change set by
reconciling `git status --short` against `git diff --cached --name-only`, count the paths, confirm
all are listed, note that the set covers release artifacts as well as feature files (the CR is
written before the release commit exists), and record which subset each review round re-examined.
Step 3.5's verification line gained a matching Files-Reviewed completeness check alongside its
existing placeholder, sentinel and version checks. The list has come up short in three consecutive
releases — corrected after 1.6.0 in `af1f8cb`, again during 1.7.0, and again in this release's own
verification — because Step 3 never named a source, so each worker listed only the file it was
told about. Still a PATCH: no new capability, a defect fix to release bookkeeping.

---

## Findings

### Critical Issues

None.

### Major Issues

- **Blanket "every structural path" clause could write settings into an uninitialized repo** —
  `plugins/trip/skills/TRIP-upgrade/SKILL.md`, Phase 0 standalone-migrations paragraph — the first
  fix attempt said the standalone migrations run on *every* structural path, which conflicts with
  the "Neither exists → point at `/TRIP-init` and stop" row. Worse, both migration conditions hold
  *vacuously* on an uninitialized project: a nonexistent `docs/TRIP.md` trivially "has no"
  bootstrap subsection, and the allowlist condition never mentioned `docs/TRIP.md` at all. An
  agent could therefore have written a git permission allowlist into `.claude/settings.json` of a
  repository TRIP was never initialized in. **Disposition: addressed, redundantly** — Phase 0 now
  carves the "Neither exists" row out explicitly, *and* each migration carries its own
  precondition (the bootstrap migration requires `docs/TRIP.md` to exist; the allowlist migration
  requires an initialized TRIP project). Either guard alone is sufficient.

### Minor Issues

- **Phase 0 probe did not match the migration's condition** — same file, Phase 0 inspection
  block — the probe grepped for `git worktree add` while the migration's condition is the
  `Bash(git worktree add:*)` entry specifically under `permissions.allow`. A project carrying that
  command as a `deny` or `ask` entry would have matched the probe and silently skipped the
  migration it still needed. **Disposition: addressed** — the probe now greps
  `Bash(git worktree add:\*)` and notes that it must sit under `permissions.allow`.
- **Frontmatter description did not mention the standalone migrations** — same file, frontmatter —
  the description listed only the legacy and routing migrations, so the skill under-advertised two
  of the four things it now does. **Disposition: addressed** — the description now names the
  worktree-bootstrap backfill and the git worktree permission allowlist alongside the existing
  branches.

### Suggestions

- **Prohibitions paired with positive targets** — the allowlist migration's closing sentence was
  phrased as a bare prohibition ("do not allowlist the destructive commands"). **Disposition:
  addressed** — rewritten as "Allowlist exactly the entries Phase 5b lists; the destructive
  commands it names stay excluded."
- **Idempotency wording** — the routing migration described a second run as exiting "without
  edits", which is no longer true now that it continues into the standalone migrations.
  **Disposition: addressed** — reworded to "sees the section and leaves it alone", with the
  hand-off stated explicitly.

---

## Checklist

- [x] 1. Functional Requirements — passed; the defect was confirmed against a real downstream
  project (`crm`: has `## Agent routing`, no legacy skills, no git allowlist — it needed the
  allowlist migration and could not reach it), and the reviewer traced five upgrade cases (A-E)
  against the edited text, including an uninitialized project and a Case C ordering interaction
  where `docs/TRIP.md` does not exist until Phase 3.1 writes it.
- [x] 2. Skill / Prompt Quality — passed; the frontmatter description now covers all four
  branches, and the one prohibition in the touched text is paired with its positive target.
- [x] 3. Architectural Compliance — passed; the change restores the routing behavior 1.7.0's wiki
  entry already claimed, and `docs/archi/pages/trip-plugin.md` is refreshed via `wiki-ingest`.
- [x] 4. Distribution & Versioning — passed; `trip` bumped 1.7.0 → 1.7.1 (patch: bug fix, no new
  capability), no other plugin touched, and `README.md` carries no version literal and no
  skill-list change.
- [x] 5. Script Correctness — not applicable; no Python or other script files changed.
- [x] 6. Cross-Reference Integrity — passed; the new hand-offs name sections that exist in the
  same file (`Worktree bootstrap migration`, `Git permission allowlist migration`,
  `TRIP-init` Phase 5b), and `wiki_lint.py` passes clean over `docs/archi/`.

---

## Verdict

**APPROVED**

Independent `code-reviewer`, two rounds. Round 1 returned REQUEST_CHANGES with 1 Major, 2 Minor
and 2 Suggestions; all five were fixed and round 2 returned APPROVED. The Major is worth
remembering: it was introduced *by the fix*, not present in 1.7.0, and it turned on two conditions
that were true vacuously rather than meaningfully — the class of defect that a path table invites
whenever a new decision is bolted onto it. It is closed with two independent guards so that
removing either one does not reopen it. As with every prompt change in this repo, no automated
harness covers this surface; per `docs/TRIP.md` § Integration checks, the real confirmation is a
live `/TRIP-upgrade` run against an already-routed project.

The `TRIP-3-release/SKILL.md` change is **not** covered by this verdict's review rounds — it was
added to the release after round 2 closed, so `code-reviewer` never saw it. Its assurance is
`release-verifier`'s check of the release artifacts, and the findings and dispositions above belong
solely to the reviewed routing fix.
