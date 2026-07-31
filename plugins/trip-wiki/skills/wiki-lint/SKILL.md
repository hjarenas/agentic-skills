---
name: wiki-lint
description: Check the architecture wiki for broken links, orphans, stale claims and contradictions, and repair what is safe to repair
disable-model-invocation: true
argument-hint: "[--fix]"
---

# Wiki Lint

Periodic health check on `docs/archi/`. Two passes: a script settles the mechanical questions,
then you spend your attention on the ones that need judgement.

Run it after a burst of ingests, before a release, or when a query turned up something the wiki
got wrong.

## Pass 1 — mechanical

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/wiki_lint.py"
```

It reports, per page: missing or malformed frontmatter, `[[links]]` that resolve to nothing,
frontmatter `links:` that disagree with the body, pages missing from `index.md`, pages nothing
links to, `superseded` pages that name no replacement, cited code paths that no longer exist,
pages past the size limit in `SCHEMA.md`, and a monolithic `log.md` where per-release log files
belong.

Exit 0 clean, 1 findings, 2 no wiki. `--json` for machine-readable output.

Do not re-derive these by hand. If the script's output is empty, the mechanical layer is fine.

## Pass 2 — semantic

These need reading, so the script leaves them to you. Read `docs/archi/index.md` and the pages
the findings point at.

1. **Contradictions.** Two pages asserting different things about the same behaviour. Check
   both against the code; the code decides. Fix the loser and note the correction in the log.

2. **Stale claims.** A page whose `verified-at` is well behind the current version, describing
   an area that has changed since. Spot-check its claims against the code. What survives gets a
   refreshed `verified-at`; what does not gets fixed, or marked `status: stale` if you cannot
   settle it now.

3. **Missing pages.** A concept several pages reference but none owns. If it keeps coming up,
   it deserves a page — write it, or list it for the user if it needs domain knowledge you
   lack.

4. **Pages that should be split.** The size check is a proxy; a page can be under the limit and
   still cover two topics. If a page's sections have no relationship to each other, split it.

5. **Pages that should be merged.** The opposite failure: two pages that are always read
   together and always edited together are one page.

## Fixing

Without `--fix`, report findings and stop.

With `--fix`, repair the unambiguous ones directly:

- broken `[[links]]` where the intended target is obvious (a rename, a split)
- `links:` frontmatter drift — reconcile to the body
- missing `index.md` entries — insert in sort position
- `superseded` pages missing their replacement link, where the log says which page replaced it

Do **not** auto-fix anything requiring judgement: contradictions, stale claims, splits, merges,
deletions. Report those and let the user decide. Wrong content confidently rewritten is worse
than wrong content flagged.

## Reporting

Group findings by severity, not by check:

- **Wrong** — the wiki asserts something the code contradicts. Fix first.
- **Broken** — links, index, frontmatter. Cheap; `--fix` handles most.
- **Drifting** — stale `verified-at`, oversized pages, missing pages. Schedule.

End with what you changed and what you left for the user.
