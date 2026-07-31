# The architecture wiki: layout, conventions, invariants

This is the shared reference for every `wiki-*` skill. It describes what a TRIP
architecture wiki *is*. The per-project variant of it lives at
`docs/archi/SCHEMA.md`, written by `wiki-init` and edited freely thereafter —
when the two disagree, `SCHEMA.md` wins, because it knows the project.

## Why not one big file

`docs/ARCHI.md` was a single document that every plan, review and
implementation read in full. It has three failure modes:

1. **It grows without bound.** Compaction fought the symptom by deleting detail
   — trading accuracy for size, permanently.
2. **Reading it costs the whole file** even when a change touches one subsystem.
3. **Every branch edits the same file**, so every merge conflicts.

A wiki of atomic pages fixes all three: pages are added rather than grown,
readers follow the index to the two or three pages they need, and two branches
working on different subsystems never touch the same file.

## Layout

```
docs/archi/
├── index.md            # the catalog — every page, one line each
├── SCHEMA.md           # this project's conventions; read by every wiki skill
├── pages/
│   ├── request-lifecycle.md
│   ├── auth-model.md
│   └── …               # one topic per file, kebab-case slug
└── log/
    ├── v0.4.0.md       # one file per release — see "Branch safety"
    └── v0.4.1.md
```

## Page format

Every page in `pages/` carries frontmatter and a body:

```markdown
---
title: Request Lifecycle
status: current
updated: 2026-07-31
verified-at: 0.4.2
links: [routing, error-handling, auth-model]
---

One-paragraph answer to "what is this and why does it exist".

## …sections as the topic needs…
```

| Field | Meaning |
| :--- | :--- |
| `title` | Human title. The slug is the filename. |
| `status` | `current` · `stale` (suspected out of date) · `superseded` (body must name the replacement) |
| `updated` | ISO date of the last edit to this page |
| `verified-at` | Project version at which the content was last checked against the code |
| `links` | Slugs of related pages. Mirrors the `[[wikilinks]]` in the body; lint reconciles the two. |

**Cite the code.** A claim about behaviour names the file that implements it —
`src/http/router.ts:88` — so lint and readers can check it. A page with no code
references is either a concept page or a page that has drifted.

**Link with `[[slug]]`.** Body links use `[[request-lifecycle]]`, resolved to
`pages/request-lifecycle.md`. This renders as a real link in Obsidian, so
`docs/archi/` can be opened as a vault with no conversion.

**Keep pages atomic.** One topic per page. A page past ~400 lines is two pages
that have not been separated yet — split it and link them. Splitting is the
replacement for compaction: nothing is deleted, the unit just gets smaller.

## index.md

The catalog. One line per page, grouped under headings, sorted by slug within
each group:

```markdown
## Runtime

- [[auth-model]] — how a request proves who it is, and what that grants.
- [[request-lifecycle]] — middleware chain from socket to response.

## Data

- [[migrations]] — how schema changes ship and roll back.
```

A reader starts here and follows the two or three links that matter. That is
the whole point: the index is the only file read in full.

## Branch safety

The wiki lives in the repo and is versioned with the code, so a branch's wiki
describes that branch's architecture — which is what you want. Two conventions
keep merges from hurting:

1. **The log is one file per release**, `log/v<x.y.z>.md`, never one appended
   file. Branches heading for different versions never touch the same log file.
   An append-only `log.md` would conflict on every single merge.

2. **`index.md` is one line per page, sorted by slug.** Two branches that each
   add a page add one line each, in different places, and git merges them
   without help. Rewriting or reordering the index wholesale destroys this —
   don't. Insert in sort position and leave the rest alone.

Worktrees need nothing special: each worktree has its own checkout, so each has
its own `docs/archi/`, and they merge like any other file.

## Obsidian

`docs/archi/` is a valid Obsidian vault as written — point Obsidian at that folder and it opens.
Nothing in the format is Obsidian-specific; the compatibility is a consequence of choices made
for other reasons (`[[slug]]` links because they survive file moves, YAML frontmatter because it
is greppable), so the wiki costs nothing to agents that have never heard of Obsidian.

Opening it buys a human three things the agent does not need:

- **Graph view** — the shape of the architecture, and which pages are hubs. An orphan or an
  over-connected god-page is visible at a glance, before lint would name it.
- **Backlinks** — "what depends on this?", answered by the wiki rather than by grep.
- **Search and canvas** — fuzzy search across pages, and canvas boards for sketching a change
  over the existing pages.

Two conventions keep it well-behaved in both directions:

- Obsidian's property editor rewrites list frontmatter into a block sequence with `[[...]]`
  wrappers. That is fine — `wiki_lint.py` reads `links: [a, b]`, `links: ["[[a]]"]`, and the
  block form identically. Edit pages in Obsidian without fear of inventing lint findings.
- Obsidian writes a `.obsidian/` settings folder into the vault. Add `docs/archi/.obsidian/` to
  `.gitignore`, or commit it deliberately to share view settings with the team — but decide,
  rather than letting it drift in as noise.

Obsidian is strictly optional. The wiki is plain markdown in the repo; the agent reads it with
Read and Grep, and so can you.

## The operating loop

| Skill | Does |
| :--- | :--- |
| `wiki-init` | Create the structure and write `SCHEMA.md` for this project |
| `wiki-migrate` | Split an existing `docs/ARCHI.md` into pages, without losing content |
| `wiki-ingest` | Fold a landed change into the wiki — update pages, add pages, fix cross-references, write the log entry |
| `wiki-query` | Answer a question from the wiki, with citations; optionally file the answer back as a page |
| `wiki-lint` | Find contradictions, stale claims, orphans, broken links and oversized pages |

Ingest is the one that keeps the wiki true; TRIP-3-release calls it on every
release. Lint is periodic maintenance. Query is how the wiki pays you back.

## Invariants lint enforces

- Every page is reachable from `index.md`.
- Every `[[link]]` resolves to a file in `pages/`.
- `links:` frontmatter and body `[[links]]` agree.
- No page contradicts another on the same fact.
- No page cites a file path that no longer exists.
- `status: superseded` pages name their replacement.
- No page exceeds the size limit in `SCHEMA.md`.
