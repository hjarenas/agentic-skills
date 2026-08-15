# Codex-heavy preset

Use this opt-in profile when Claude Opus should own discovery/planning and Codex should own every
downstream worker role. `opus` is the native Claude harness alias; the Codex values are runtime
model IDs.

| Role | Harness | Model | Effort |
| :--- | :--- | :--- | :--- |
| discovery | subagent | opus |  |
| planner | subagent | opus |  |
| plan-reviewer | codex-bridge | gpt-5.6-sol |  |
| implementer | codex-bridge | gpt-5.6-luna |  |
| batch-reviewer | codex-bridge | gpt-5.6-sol |  |
| fixer | codex-bridge | gpt-5.6-terra |  |
| test-worker | codex-bridge | gpt-5.6-luna |  |
| code-reviewer | codex-bridge | gpt-5.6-sol |  |
| workspace-worker | codex-bridge | gpt-5.6-luna |  |
| release-worker | codex-bridge | gpt-5.6-luna |  |
| release-verifier | codex-bridge | gpt-5.6-luna |  |

Copy this table into `docs/TRIP.md`'s `Agent routing` section (replacing the default table) to
adopt it for a project, or pass the equivalent `--model`/`--harness` invocation overrides for a
single run without changing the project's default.
