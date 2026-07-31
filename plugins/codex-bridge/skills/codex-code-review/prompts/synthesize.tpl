The iteration loop has converged (or been capped). Produce a **consolidated final review** for archival.

This is the canonical record of how this change was reviewed. Cover every finding from the whole thread — addressed, overridden, or open — with final status and `file:line` references.

This is a fresh Codex run, so the last review of the loop is reproduced below. Combine it with
the round-by-round summary the requester supplies in the additional-context block.

## Format

Read `docs/3-code-review/cr-template.md` and produce output conforming to its markdown skeleton. That file is project-local and was tailored to this codebase by TRIP-init.

Fill-in guide:
- **Title**: feature/change name from `{{TARGET}}`
- **Review Date**: today's date (YYYY-MM-DD)
- **Version**: leave as `<x.y.z>` (requester fills from TRIP-2 Step 2)
- **Files Reviewed**: from `git diff --name-only HEAD`
- **Plan**: `{{TARGET}}` if path under `docs/1-plans/`, else "no plan — unplanned change"
- **Findings**: every finding from all rounds with `file:line` and disposition
- **Checklist**: tick passing sections, caveat the rest
- **Verdict**: `APPROVED` / `APPROVED with observations` / `NEEDS REVISION`

Output only the rendered markdown — no preamble or commentary.

## Final review of the loop

{{PRIOR_REVIEW}}

## Sentinel

After the review, on its own line: `PROMOTION_READY`

{{EXTRA_PROMPT}}
