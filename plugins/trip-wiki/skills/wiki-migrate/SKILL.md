---
name: wiki-migrate
description: Split an existing monolithic docs/ARCHI.md into a docs/archi/ wiki without losing content
disable-model-invocation: true
---

# Wiki Migrate

Convert a project's `docs/ARCHI.md` into an architecture wiki. This is a one-way, one-time
migration; afterwards `/wiki-ingest` keeps the wiki current and `ARCHI.md` is gone.

Read [`../../references/wiki-spec.md`](../../references/wiki-spec.md) first.

**Nothing is dropped.** The point of the wiki is that pages get *split* instead of compacted,
so a migration that summarises is a migration that loses the very detail the wiki exists to
keep. If `ARCHI.md` was previously compacted, the detail it lost is not recoverable here —
say so, and offer to re-derive the thinnest sections from the code as a follow-up.

## Step 1 — check the ground

- No `docs/ARCHI.md` → the project has nothing to migrate; use `/wiki-init`.
- `docs/archi/` already exists → stop and report. Do not merge into a live wiki blindly.
- Uncommitted changes to `docs/ARCHI.md` → ask the user to commit or stash first. This
  migration rewrites the file's entire neighbourhood and a clean diff is how they review it.

## Step 2 — read ARCHI.md in full

The last time it will be read in full. Note its section structure, its terminology, and the
project version it describes.

Measure it: `wc -l docs/ARCHI.md`. Report the size so the before/after is concrete.

## Step 3 — derive the taxonomy

Group ARCHI's sections into the page groups this project needs. Sections usually map to pages
close to one-to-one, with two adjustments:

- A section over the size limit becomes several pages. Split on its natural seams — subsections
  that stand alone — not at an arbitrary line count.
- Several thin, tightly-coupled sections become one page. Three paragraphs that are always read
  together are one topic.

Then create the structure and write `docs/archi/SCHEMA.md` following `/wiki-init` Step 4, using
**ARCHI's own vocabulary** — if it says "peripherals", the taxonomy says peripherals.

## Step 4 — write the pages

One page per topic, in the format from `wiki-spec.md`. For each:

- `title` from the section heading
- `status: current`
- `updated`: today
- `verified-at`: the project's current version
- `links`: the pages this one relates to — derived from ARCHI's cross-references and from what
  the content actually depends on

Move the content across **verbatim** where it is already dense. Rewrite only to fix references
that no longer make sense out of their original context ("as described above" must become
`[[an-actual-page]]`).

Preserve mermaid diagrams intact, on the page whose topic they illustrate. A diagram spanning
several pages' topics goes on the most general one, linked from the others.

## Step 5 — write index.md

One line per page, grouped by the taxonomy, sorted by slug within each group. The one-line
summaries are new writing — ARCHI has no equivalent — so make them say what question the page
answers, not what it is called.

## Step 6 — first log entry

`docs/archi/log/v<current-version>.md`:

```markdown
# v<x.y.z>

## <today> — migrated from ARCHI.md

Split docs/ARCHI.md (<N> lines) into <M> pages. No content dropped.

Pages added: <slug>, <slug>, …
```

## Step 7 — verify before deleting

Run the mechanical check:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/wiki_lint.py"
```

Then verify coverage yourself: walk ARCHI.md's section list and confirm each one landed
somewhere. Report any section you deliberately dropped, with the reason.

**Only then** remove `docs/ARCHI.md`, and update the references to it:

- `docs/ARCHI-rules.md` → rewrite to describe maintaining the wiki via `/wiki-ingest`, or
  delete it, since `SCHEMA.md` now holds those rules
- any `AGENTS.md` / `CLAUDE.md` / README pointing at `docs/ARCHI.md`
- `grep -rln "ARCHI.md" --exclude-dir=.git .` to catch the rest

The deletion is a separate, reviewable commit from the page creation. Say so to the user.

## Step 8 — report

Before/after line counts, the page list, the coverage walk from Step 7, and anything
`ARCHI.md` claimed that you could not ground in the code (write those pages `status: stale`
rather than silently laundering them into fresh-looking pages).
