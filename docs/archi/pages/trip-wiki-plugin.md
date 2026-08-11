---
title: trip-wiki plugin
status: current
updated: 2026-08-11
verified-at: 1.1.0
links: [distribution, trip-plugin]
---

The architecture-memory system: atomic linked pages under a consuming project's `docs/archi/`,
replacing a single monolithic `ARCHI.md`. This very page lives in exactly that structure — this
repo's own `docs/archi/` was built by `wiki-init`, and is versioned like any other plugin's
output (see [[distribution]]).

## Why atomic pages instead of one file

`plugins/trip-wiki/references/wiki-spec.md` names three failure modes of a single `ARCHI.md`: it
grows without bound (compaction only trades accuracy for size), reading it costs the whole file
even for a one-subsystem change, and every branch edits the same file so every merge conflicts.
Splitting into `pages/<slug>.md` plus an `index.md` catalog fixes all three — pages are *added*
rather than grown, a reader follows two or three links instead of loading everything, and two
branches adding different pages never touch the same file.

## The five skills

| Skill | Model-invokable | Does |
| :--- | :--- | :--- |
| `wiki-init` | No | Creates `docs/archi/`, writes the project's `SCHEMA.md`, seeds first pages — asks for taxonomy approval before anything downstream trusts it |
| `wiki-migrate` | No | One-time: splits an existing monolithic `ARCHI.md` into pages, nothing dropped |
| `wiki-ingest` | Yes | Folds a **landed** change into the wiki — the only skill that keeps it true; [[trip-plugin]]'s `TRIP-3-release` calls it every release |
| `wiki-lint` | Yes | Two-pass health check: `wiki_lint.py` settles mechanical questions (broken links, orphans, size), the model handles what needs judgment (contradictions, staleness) |
| `wiki-query` | Yes | Answers an architecture question from the wiki with citations; optionally files the answer back as a page |

## Branch safety

Two conventions specifically prevent merge conflicts: the log is **one file per release**
(`log/v<x.y.z>.md`, never a single appended file), and `index.md` is one line per page **sorted
by slug** — two branches adding different pages add different lines in different positions and
git merges them without help. Rewriting the index wholesale destroys this.

## Obsidian compatibility is a side effect, not a design goal

Double-bracket wikilinks and YAML frontmatter were chosen because they survive file moves and stay
greppable — the fact that `docs/archi/` opens as a valid Obsidian vault follows from those
choices, not the other way around. The wiki costs nothing to an agent that has never heard of
Obsidian.
