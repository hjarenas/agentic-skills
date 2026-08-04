# Agent routing contract

TRIP skills are **orchestrators**, not workers. The active agent coordinates the workflow but
never performs phase work itself.

## Orchestrator boundary

The orchestrator may:

- read `docs/TRIP.md`, plans, worker reports, and repository status needed to route work;
- split work into batches, select roles, dispatch workers, and pass artifacts between them;
- relay questions that require user judgement;
- evaluate explicit completion tags and gate results; and
- stop, retry, or reroute a failed assignment.

The orchestrator must not:

- explore or analyze the codebase as a substitute for an assigned discovery worker;
- write or edit plans, code, tests, review findings, or release documentation;
- run lint, builds, tests, version updates, commits, pushes, or release commands;
- review a diff or fix a worker's findings; or
- use a "small" or "trivial" exception to do worker tasks directly.

If no suitable worker can be launched, stop and report the missing capability. Do not silently
fall back to doing the work in the orchestrator context.

## Roles

| Role | Owns | Must not own |
| :--- | :--- | :--- |
| `discovery` | Architecture/wiki/graph/code exploration and an evidence report | Plan decisions or edits |
| `planner` | Clarification draft, assumptions, and the plan document | Plan approval or implementation |
| `plan-reviewer` | Independent plan findings and verdict | Editing the plan it reviews |
| `implementer` | A scoped implementation batch | Reviewing or approving its own batch |
| `batch-reviewer` | Delta review and concrete fix instructions | Editing the reviewed batch |
| `fixer` | Corrections requested by a reviewer | Approving those corrections |
| `test-worker` | Test authoring and execution of the requested gate | Code-review verdict |
| `code-reviewer` | Independent full-change review and verdict | Editing the change it reviews |
| `workspace-worker` | Branch checkout/creation, staging, commits, pushes, and status reports | Product changes or approval verdicts |
| `release-worker` | Version/docs/changelog/commit/PR preparation | Declaring an unverified implementation ready |
| `release-verifier` | Verify release artifacts, branch safety, and PR readiness | Producing the release artifacts it verifies |

Keep reviewer roles independent from the worker whose artifact they review. A worker may be
reused across batches of the same kind, but do not use the implementer as `batch-reviewer` or
`code-reviewer`, the planner as `plan-reviewer`, or the release worker as `release-verifier`.

## Routing configuration

Read `docs/TRIP.md` section `Agent routing`. A new project receives this shape:

```markdown
## Agent routing

Invocation arguments override this table for the current run. Blank model or effort means the
harness default.

| Role | Harness | Model | Effort |
| :--- | :--- | :--- | :--- |
| discovery | subagent |  |  |
| planner | subagent |  |  |
| plan-reviewer | codex-bridge |  |  |
| implementer | codex-bridge |  |  |
| batch-reviewer | subagent |  |  |
| fixer | subagent |  |  |
| test-worker | subagent |  |  |
| code-reviewer | codex-bridge |  |  |
| workspace-worker | subagent |  |  |
| release-worker | subagent |  |  |
| release-verifier | subagent |  |  |
```

Supported harness values:

- `subagent`: launch a native harness sub-agent and include the selected model/effort when the
  harness supports those fields.
- `codex-bridge`: invoke the role mapping below. Pass model/effort as explicit per-run overrides;
  do not mutate `.codex/config.toml`.
- `skill:<name>`: invoke the named installed worker skill, including the role, artifact, scope,
  completion contract, and requested model/effort in the assignment.

An invocation may begin with routing overrides:

```text
--harness <role>=<harness> --model <role>=<model> --effort <role>=<effort> <task>
```

Allow multiple overrides. Strip them from the task before dispatch. Precedence is:

1. invocation override;
2. `docs/TRIP.md` role row;
3. the defaults in the table above.

Reject an unknown role or harness with a clear error. If a requested model is unavailable in the
selected harness, ask the user to choose another model or harness; never substitute silently.

### Codex bridge role mapping

| Role | Skill | Access | Completion tags |
| :--- | :--- | :--- | :--- |
| plan-reviewer | `codex-plan-review` | read-only | `APPROVED`, `REQUEST_CHANGES`, `NEEDS_REWORK` |
| implementer | `codex-implement` | write | `IMPLEMENTATION_COMPLETE`, `IMPLEMENTATION_PARTIAL` |
| batch-reviewer | `codex-batch-review` | read-only | `BATCH_APPROVED`, `BATCH_REQUEST_FIXES` |
| fixer | `codex-fix` | write | `FIX_COMPLETE`, `FIX_PARTIAL` |
| test-worker | `codex-test` | write | `TESTS_GREEN`, `TESTS_RED` |
| code-reviewer | `codex-code-review` | read-only | `APPROVED`, `REQUEST_CHANGES`, `NEEDS_REWORK` |
| workspace-worker | `codex-workspace` | restricted write | `WORKSPACE_COMPLETE`, `WORKSPACE_BLOCKED` |
| release-worker | `codex-release` | restricted write | `RELEASE_COMPLETE`, `RELEASE_BLOCKED` |
| release-verifier | `codex-release-verify` | read-only | `RELEASE_APPROVED`, `RELEASE_REQUEST_CHANGES` |

`discovery` and `planner` intentionally have no Codex bridge mapping: their default `subagent`
harness keeps repository discovery and user-facing planning in the primary harness. Selecting
`codex-bridge` for either is an unsupported routing error; use `subagent` or `skill:<name>`.

For every bridge call, use a role-specific state target such as `<plan>#batch-review-2` or
`<plan>#test-full-r1`. The bridge stores output by target; reusing the bare plan path across roles
can overwrite another worker's report.

### Codex-heavy preset

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

## Dispatch contract

Every assignment must include:

1. role and harness/model/effort selection;
2. exact input artifacts and scoped objective;
3. allowed write paths or a read-only constraint;
4. verification expected from that worker; and
5. a completion tag and concise report format.

The orchestrator consumes reports, not hidden worker context. Carry decisions, corrections, and
open findings explicitly into every subsequent assignment. Dispatch independent roles in
parallel when the harness permits it; serialize roles that consume one another's artifacts.
