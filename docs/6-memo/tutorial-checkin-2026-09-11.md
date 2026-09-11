# One-month check-in: per-release tutorials (2026-09-11)

## Current setting (`docs/TRIP.md` § Tutorials)

- **Enabled**: yes
- **Level**: intermediate
- **Focus**: Claude Code plugin/skill mechanics; the tooling this repo builds (TRIP, the
  architecture wiki, codex-bridge internals)
- **Style**: concise

Enabled at `/TRIP-init` time on 2026-08-11, on a trial basis, with a note to revisit around
2026-09-11.

## Releases since 2026-08-11

Four releases have shipped since the trial started (`docs/2-changelog/changelog_table.md`):

| Version | Date | Week |
| --- | --- | --- |
| 0.2.0 | 2026-08-15 | 1 |
| 1.6.0 | 2026-08-20 | 2 |
| 1.7.0 | 2026-08-23 | 2 |
| 1.7.1 | 2026-08-24 | 3 |

## Tutorials actually generated

**Zero.** `docs/5-tuto/` does not exist in the repository — no tutorial file has ever been
created there.

This is not a case of "no releases yet, too early to tell": the release flow has had four
opportunities to generate a tutorial and produced none.

## Why: this isn't a stale setting, it's a wiring gap

Checked whether the Tutorials step was added to `TRIP-3-release` only recently (i.e., after
some releases had already run without it): it was not. `Step 8: Tutorial` has been part of
`TRIP-3-release`'s skill content since the very first commit (`4c2e3fd`, 2026-07-31), predating
even `/TRIP-init`, and `docs/TRIP.md`'s `Tutorials — Enabled: yes` has been present since the
initial commit (`90c7d37`, 2026-08-11) through every release since, unchanged. So on paper, all
four releases should have reached Step 8 and produced a `docs/5-tuto/tuto_x.y.z.md` file — none
did.

That means the trial hasn't actually been exercised: the data isn't "tutorials weren't worth
generating" or "tutorials generated but low quality", it's "the step that's supposed to fire is
apparently not firing (or its output isn't landing where expected), for four releases running."

## Recommendation

**Do not disable the trial, and do not adjust level/focus/style** — there's no usable signal yet
on whether the *content* of tutorials is worth keeping, because none have been produced to
evaluate. Disabling now would be guessing.

Instead, the maintainer should treat this as a bug report on the release flow: re-run (or dry-run)
`TRIP-3-release` for a small change and confirm Step 8 actually triggers and writes a file under
`docs/5-tuto/`. Once that's confirmed working, let it run for a few more real releases before the
next check-in, since the "is this worth keeping" question can't be answered until there's at
least one tutorial to look at.

Suggested next check-in: after Step 8 is confirmed to fire and 2-3 tutorials have actually been
generated, or in another month if the wiring issue turns out to need more investigation.
