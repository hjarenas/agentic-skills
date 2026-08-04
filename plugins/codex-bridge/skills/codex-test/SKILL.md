---
name: codex-test
description: Author scoped tests when requested and execute a TRIP micro-gate or full testing gate
---

# Codex Test Worker

Use a unique target such as `<plan-path>#test-full-r1`. Parse model/effort and invoke
`codex-run.py` with `--write`, `prompts/test.tpl`, and the exact gate scope in `--extra`.
Write access is required for requested tests and mechanical test-only corrections; do not modify
product code to conceal a failure.

Parse `TESTS_GREEN` or `TESTS_RED`. Return commands, counts, new tests, failures, and artifacts.
Support runtime `show` and `reset` actions.
