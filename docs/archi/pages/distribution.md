---
title: Distribution
status: current
updated: 2026-08-11
verified-at: 79fbba0
links: [trip-plugin, trip-wiki-plugin, codex-bridge-plugin, pocock-core-plugin, toolbox-plugin]
---

How `agentic-skills` packages and ships itself as installable Claude Code plugins, and how the
one vendored plugin (`pocock-core`) stays in sync with its upstream source without drifting into
a silent fork.

## The marketplace

`.claude-plugin/marketplace.json` declares this repo as a marketplace named
`hjarenas-agentic-skills`, listing five plugins by `source` path (`./plugins/<name>`). A user adds
it once (`/plugin marketplace add hjarenas/agentic-skills`) and installs plugins individually
(`/plugin install <name>@hjarenas-agentic-skills`).

Each plugin carries its **own** `plugins/<name>/.claude-plugin/plugin.json` with its own semver
`version` — there is no repo-wide version. A change to files under `plugins/trip/` bumps
[[trip-plugin]]'s version; it does not touch [[trip-wiki-plugin]]'s. `README.md`'s plugin table
is the human-readable index of what each plugin ships — [[codex-bridge-plugin]] and
[[toolbox-plugin]] included — and must stay in sync when a plugin's skill list changes.

**Cross-plugin invocation.** `${CLAUDE_PLUGIN_ROOT}` resolves to the *calling* plugin's own
install path — each plugin lives in its own versioned cache directory
(`~/.claude/plugins/cache/hjarenas-agentic-skills/<name>/<version>/`), so one plugin's skill
cannot reach another plugin's files by path through that variable. Skills invoke each other **by
name** instead (e.g. `TRIP-3-release` invoking `wiki-ingest`) and rely on the harness to resolve
the target plugin. `TRIP-3-release`'s own notes call this out explicitly after getting it wrong
once.

**Plugin installation is per-machine, per-project, and does not include the source repo itself.**
Installing `trip@hjarenas-agentic-skills` for `some-other-project` does not make it available
when working *inside* `agentic-skills` — this repo authors the plugins, it doesn't automatically
consume them. Working on skill content in this repo requires installing the plugins for this
project too (`--scope local`, to keep the enablement out of the tracked `.claude/settings.json`).

## Vendoring (`pocock-core`)

`pocock-core` is a curated subset of [mattpocock/skills](https://github.com/mattpocock/skills),
copied in rather than depended on live — read-only marketplace plugins can't be wired into TRIP
(see [[pocock-core-plugin]] for why that matters). `plugins/pocock-core/UPSTREAM.json` pins the
upstream commit each vendored file came from and lists every vendored file with its SHA-256.

`scripts/vendor-sync.py` uses that pin as a **merge base**: for each file it does a real 3-way
merge of `base` (upstream at the pinned commit), `ours` (the file as it exists here, possibly
locally edited), and `theirs` (upstream at the new commit). Untouched files fast-forward
silently; edited files merge via `git merge-file`; only genuinely overlapping edits produce
conflict markers. A file renamed or restructured upstream (e.g. `writing-great-skills` →
`writing-for-agents`, folding `GLOSSARY.md` into `SKILL.md`) is reported as "removed or renamed"
and must be reconciled by hand — the script does not attempt to detect renames.

**Gotcha, fixed 2026-08-11:** the upstream cache at `.vendor-cache/skills/` is `git clone --bare`,
which sets no fetch refspec. A plain `git fetch --all` after the initial clone downloaded objects
into `FETCH_HEAD` without ever advancing `refs/heads/main`, so `--check` could report "unchanged"
indefinitely regardless of how stale the pin actually was. `ensure_clone()`
(`scripts/vendor-sync.py:50`) now fetches with explicit refspecs
(`+refs/heads/*:refs/heads/*`, `+refs/tags/*:refs/tags/*`).
