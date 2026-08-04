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
- `codex-bridge`: invoke the matching `codex-*` skill. Pass model/effort as explicit per-run
  overrides to its runtime; do not mutate `.codex/config.toml`.
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
