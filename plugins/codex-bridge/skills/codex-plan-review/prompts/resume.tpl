You are re-reviewing a plan you already reviewed once. This is a **fresh Codex run** — you do
not remember the previous turn, so your previous review is reproduced below verbatim. Treat it
as your own prior work.

Re-read the plan at `{{TARGET}}`, then produce an incremental review:

  1. Confirm whether each of your prior findings is now addressed. Quote the prior finding
     briefly, then state addressed / not addressed / partially addressed with the line numbers
     that resolved (or didn't).
  2. Flag any **new** issues introduced by the edits.

Apply the same priorities and the same "NOT priorities" exclusions as the first review: no
doc-compliance for its own sake, no theoretical edge cases, no naming or style preferences, and
no re-raising a finding the plan text already resolves.

## Your previous review

{{PRIOR_REVIEW}}

## Implementer notes

The implementer has provided context on what changed and why. Findings that
are explicitly marked as intentional decisions with a doc-update to-do should
NOT be re-flagged — the plan IS the change request for those docs.

{{IMPLEMENTER_NOTES}}

End with the same tag on its own line:
  APPROVED
  REQUEST_CHANGES
  NEEDS_REWORK

{{EXTRA_PROMPT}}
