---
name: wiki-ingest
description: Fold a landed change into the architecture wiki — update affected pages, add new ones, fix cross-references and write the log entry
argument-hint: "<version | plan path | description of what changed>"
---

# Wiki Ingest

Fold a change that has **landed** into `docs/archi/`. This is the operation that keeps the wiki
true; everything else in the wiki is maintenance or reading.

Ingest runs after the work is done — from `TRIP-3-release`, or by hand after an unplanned
change. Ingesting a plan that has not been implemented writes fiction into the wiki.

Read `docs/archi/SCHEMA.md` first for this project's taxonomy, naming and size limit. Read
[`../../references/wiki-spec.md`](../../references/wiki-spec.md) for the page format and the
branch-safety rules.

## Step 1 — establish what changed

From the argument:

- **A version** (`0.4.2`) — read `docs/2-changelog/` for that version and `git diff` its tag range.
- **A plan path** (`docs/1-plans/F_*.plan.md`) — read the plan, then `git diff` the work that implemented it.
- **A description** — take it at face value, but confirm against `git diff HEAD` or the recent log.

You need the actual diff, not just the description. The wiki records what the code does, and
only the diff knows that.

## Step 2 — find the blast radius

Read `docs/archi/index.md`, then open the pages the change could touch. A single change
typically affects more pages than it changes files: a new auth header touches the auth page,
the request-lifecycle page, and any integration page that describes a caller.

Search the wiki for the identifiers in the diff — `grep -rn "<symbol>" docs/archi/pages/` finds
pages that cite code you just moved or renamed.

## Step 3 — apply the change to the wiki

In one pass, in this order:

1. **Update existing pages.** Rewrite the affected sections. Refresh `updated` and
   `verified-at` frontmatter. If a page said something now false, fix it — do not append a
   correction below the falsehood.
2. **Add new pages** for subsystems the change introduced. Follow `SCHEMA.md` naming and the
   page template. Ground every claim in code you read.
3. **Split any page** that crossed the size limit in `SCHEMA.md`. Splitting is how this wiki
   stays readable — never compress a page to fit. The old slug keeps the general topic; the
   extracted slug takes the specific one, and each links to the other.
4. **Fix cross-references.** Every page that linked to a renamed or split page needs its
   `[[links]]` and its `links:` frontmatter updated. This is the step most often skipped and
   the one lint most often catches.
5. **Mark superseded content.** If the change replaced an approach outright, set the old page's
   `status: superseded` and name the replacement in its body. Do not delete it — the reason the
   old approach lost is worth keeping.

## Step 4 — update index.md

Add one line per new page, **inserted in sort position** within its group. Update the one-line
summary of any page whose purpose shifted. Do not reorder or rewrite the whole file — see
`wiki-spec.md` §Branch safety.

## Step 5 — write the log entry

Append to `docs/archi/log/v<version>.md`, creating it if this is the first entry for that
version. One file per release, never a single global log:

```markdown
## <YYYY-MM-DD> — <short title>

<what changed in the architecture, in two or three sentences>

Pages updated: [[slug]], [[slug]]
Pages added: [[slug]]
Superseded: [[slug]] → [[replacement]]
```

If the wiki has no `version` to hang the entry on (unreleased work), use the version the change
is heading for. TRIP-3-release bumps it before calling this skill, so the file will match.

## Step 6 — report

Tell the user: pages updated, pages added, pages split, cross-references fixed, and anything in
the diff you chose **not** to record with the reason. Silence about a skipped subsystem is how
wikis rot.

## Notes

- Ingest is additive by default. The only content that leaves the wiki is content that was
  wrong; content that is merely old becomes `superseded`.
- If the change makes a claim you cannot verify in the code, say so in the report and mark the
  page `status: stale` rather than writing a guess.
- Running ingest twice for the same change is safe — the second run finds the pages already
  current and says so.
