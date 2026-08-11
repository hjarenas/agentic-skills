---
title: pocock-core plugin
status: current
updated: 2026-08-11
verified-at: 1.0.0
links: [distribution]
---

A curated, vendored subset of [Matt Pocock's `skills` repo](https://github.com/mattpocock/skills) —
copied in via `scripts/vendor-sync.py` rather than installed as his live marketplace plugin. See
[[distribution]] for the sync mechanism; this page is about *what's here* and *why vendored*.

## Why vendored, not subscribed

Pocock's own plugin (`/plugin install mattpocock-skills`) is the lower-maintenance choice for most
people — always current, zero sync burden. It's read-only, though, and can't be wired into
`trip` (`TRIP-3-release` invoking `wiki-ingest` needs a same-repo skill to invoke, not an
independently-versioned external plugin). Vendoring trades that convenience for control; the cost
is drift, which `UPSTREAM.json`'s pinned-commit merge base exists to bound. **Do not run both
`pocock-core` and `mattpocock-skills`** — every skill would be installed twice.

## What's vendored (8 requested + 3 dependencies)

| Skill | Why |
| :--- | :--- |
| `grill-with-docs` | Interviews one question at a time until the thinking holds — fills the gap before `TRIP-1-plan` starts writing |
| `to-spec` | Synthesizes a spec without re-interviewing |
| `to-tickets` | Cuts tracer-bullet slices with explicit blocking edges |
| `triage` | State-machine labeling for an issue tracker |
| `research` | Structured spike/investigation, distinct from `TRIP-research` |
| `wayfinder` | Handles work too large for one session |
| `teach` | Stateful, multi-session teaching workspace — "learn a new topic" |
| `writing-for-agents` | The reference this repo's own skills are written against (renamed from `writing-great-skills`, itself renamed from `write-a-skill`, upstream) |
| `grilling`, `domain-modeling`, `setup-matt-pocock-skills` | Pulled in as dependencies of the above, not independently requested |

## Staying current

`plugins/pocock-core/UPSTREAM.json` records the pinned upstream commit and a SHA-256 per vendored
file. `python3 scripts/vendor-sync.py --check` reports drift without writing; running it for real
does a 3-way merge per file and advances the pin only if nothing was left conflicted. A skill that
upstream **renamed or restructured** (not just edited) is reported as "removed or renamed" and
needs manual reconciliation — most recently `writing-great-skills` → `writing-for-agents`
(`GLOSSARY.md` folded into `SKILL.md`, a new `SKILL-MECHANICS.md` split out), synced 2026-08-11.

Hand-editing a vendored file without updating `UPSTREAM.json`'s stored hash makes the next sync
either silently overwrite the edit or falsely report it as a local modification — treat
`UPSTREAM.json` as authoritative, always synced through the script.
