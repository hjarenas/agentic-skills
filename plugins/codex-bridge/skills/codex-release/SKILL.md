---
name: codex-release
description: Prepare scoped TRIP release artifacts and perform explicitly authorized release push and pull-request work (the release commit belongs to `codex-workspace`)
---

# Codex Release Worker

Use a unique target such as `<plan-path>#release-prepare`. Parse model/effort and invoke
`codex-run.py` with `--write`, `prompts/release.tpl`, and exact release steps in `--extra`.

Separate preparation from externally mutating steps. Push and PR creation require explicit scope;
tagging and merging are forbidden unless independently authorized. Parse `RELEASE_COMPLETE` or
`RELEASE_BLOCKED`. Support runtime `show` and `reset` actions.
