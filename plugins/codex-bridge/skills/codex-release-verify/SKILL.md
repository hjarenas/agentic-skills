---
name: codex-release-verify
description: Independently verify TRIP release artifacts, branch safety, and pull-request readiness without editing them
---

# Codex Release Verify

Use a unique target such as `<plan-path>#release-verify-r1`. Parse model/effort and invoke
`codex-run.py` read-only with `prompts/verify.tpl` and expected state in `--extra`.

Do not pass `--write`. Parse `RELEASE_APPROVED` or `RELEASE_REQUEST_CHANGES`. Support runtime
`show` and `reset`; return findings verbatim for the release-worker.
