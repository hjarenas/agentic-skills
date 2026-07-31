---
name: wiki-query
description: Answer an architecture question from the wiki with citations, and optionally file the answer back as a page. Use when someone asks how a part of the system works.
argument-hint: "<question>"
---

# Wiki Query

Answer a question about how this system works, from `docs/archi/`, with citations.

The point is not search — it is that the answer has already been synthesised. The
cross-references exist, the contradictions were flagged at ingest, and the page you land on
reflects everything that has been folded in so far. You read three pages instead of re-deriving
the answer from the whole codebase.

## Process

1. **Read `docs/archi/index.md`.** It is the only file read in full. Pick the two or three
   pages whose one-line summaries bear on the question.

2. **Read those pages, then follow their `[[links]]`** one hop where the question needs it.
   Stop when the question is answered — pulling the whole wiki into context defeats the purpose.

3. **Answer with citations.** Every claim names the page it came from, and where the page cites
   code, pass that through: "requests are authenticated in the middleware chain before routing
   ([[request-lifecycle]], `src/http/router.ts:88`)".

4. **Check the answer against the code** when the question is load-bearing — a decision hangs
   on it, or the pages are old. If the code disagrees with the wiki, the code is right: say so
   plainly, and offer to run `/wiki-ingest` to fix the drift. A wiki that is quietly wrong is
   worse than no wiki.

5. **Say when you don't know.** If no page covers it, answer from the code and say the wiki has
   a gap. Then offer step 6.

## Step 6 — file the answer back (optional)

When the answer required real work — reading several subsystems, reconciling pages, tracing
something non-obvious — that work should not evaporate. Offer to file it:

- If it belongs on an existing page, add it there and refresh the page's `updated` field.
- If it is its own topic, write a new page per `SCHEMA.md`, add it to `index.md` in sort
  position, and link it from the pages it relates to.

This is what makes the wiki compound: exploration lands in it, not just implementation.

Do not file trivia. A question answered by one sentence on one existing page has nothing to
add back.

## Notes

- Read-only by default. Filing back (step 6) is the one write, and it is offered, not assumed.
- If `docs/archi/` does not exist, say so and point at `/wiki-init` or `/wiki-migrate` rather
  than silently answering from the codebase — the user should know the wiki is missing.
