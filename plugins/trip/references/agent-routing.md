# Agent routing contract

TRIP skills are **orchestrators**, not workers. The active agent coordinates the workflow but
never performs phase work itself.

## Orchestrator boundary

The orchestrator may:

- read `docs/TRIP.md`, plans, worker reports, and repository status needed to route work;
- split work into batches, select roles, dispatch workers, and pass artifacts between them;
- relay questions that require user judgement;
- evaluate explicit completion tags and gate results; and
- stop, retry, or reroute a failed or silent assignment as described in `Waiting for a worker`.

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
| `workspace-worker` | Branch checkout/creation, worktree add/remove and `--no-ff` merges for the flow and phase lifecycle, staging, commits, pushes, and status reports | Product changes or approval verdicts |
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

- `subagent`: launch a native harness sub-agent, using the `trip`-plugin agent named after the
  role itself (`trip:discovery`, `trip:planner`, `trip:plan-reviewer`, `trip:implementer`,
  `trip:batch-reviewer`, `trip:fixer`, `trip:test-worker`, `trip:code-reviewer`,
  `trip:workspace-worker`, `trip:release-worker`, `trip:release-verifier`) — never
  `general-purpose` and never `Explore` or another narrow read-only search agent. Each named agent
  already carries that role's read/write boundary (a role with no file-content-editing needs, or
  that only reviews, has `Write`/`Edit` denied — including `workspace-worker`, which edits no
  file content at all, only runs git commands against it), so a role dispatched through the wrong
  agent fails structurally rather than only by convention — `general-purpose`'s unrestricted
  access and `Explore`'s read-only, narrow-search scope both blur that boundary, and `Explore`'s
  own description disqualifies it for open-ended discovery, design-doc auditing, or cross-file
  consistency work regardless. Include the selected model/effort when the harness supports those
  fields.

  **Upgrade note**: these named agents ship as `plugins/trip/agents/*.md`, auto-discovered like
  skills — a project running an older cached `trip` install (before this file existed) will not
  have them yet, and a dispatch to `trip:<role>` fails with an "Unknown agent" error, the same
  failure class as an un-reloaded skill (the repo `README.md`'s "codex-bridge" install step notes
  the identical symptom for a plugin whose skills haven't registered yet). That error is
  diagnostic, not a routing dead end: retry the *same* dispatch
  with `general-purpose` instead for this one call, tell the user the `trip` plugin needs
  `/plugin marketplace update` (or a fresh install) followed by `/reload-plugins` or a full
  restart, and say so explicitly in your report rather than silently falling back for the rest of
  the run — once reloaded, later dispatches in the same session pick up the real named agents
  again without further action. No project's `docs/TRIP.md` needs editing for this upgrade; the
  subagent-type choice lives here, not in the per-project routing table.
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

Every codex-bridge role is **stateless**: each turn is a fresh process with no memory of earlier
turns, so continuity travels only through `--notes` and the stored review/report each skill reads
back in. Skills below say "stateless" and assume this definition — always pass `--notes` on
resume, or the next turn re-raises findings already settled.

`discovery` and `planner` intentionally have no Codex bridge mapping: their default `subagent`
harness keeps repository discovery and user-facing planning in the primary harness. Selecting
`codex-bridge` for either is an unsupported routing error; use `subagent` or `skill:<name>`.

For every bridge call, use a role-specific state target such as `<plan>#batch-review-2` or
`<plan>#test-full-r1`. The bridge stores output by target; reusing the bare plan path across roles
can overwrite another worker's report.

### Codex-heavy preset

An opt-in profile for projects that want Claude Opus on discovery/planning and Codex on every
downstream worker role — most projects never adopt it. See `codex-heavy-preset.md` in this
directory for the full table and how to adopt it.

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
Independent roles explicitly include independent implementation phases: dispatch one isolated
batch loop per phase in the current dependency frontier, in parallel when the harness permits it.

**Scope every worker-run test command explicitly** — never leave a `test-worker` (or an
`implementer`/`fixer` running its own verification) to decide how much of the suite to run. A
`subagent`-harness worker's own long-running command is subject to the Bash tool's force-background
past ~600s, and a backgrounded run cannot wake the worker that dispatched it — the turn ends with
no result, not a slow one. Keep every routine per-batch invocation well under that ceiling by
scoping it to the change; reserve a full-suite run for exactly one dedicated, orchestrator-owned
dispatch (per phase or per feature), never as implicit self-verification inside every worker's
turn. Require the report to state the selected/affected test count — a project's auto-marking or
an over-broad exclusion filter can silently deselect everything a scoped run was supposed to
cover, so treat a count of 0 as a failed gate, not a clean pass.

If a role's routing-table model/effort is consistently overridden per dispatch because the
configured default proves unreliable for that role, update `docs/TRIP.md`'s routing table to match
observed reality rather than continuing to override it on every call — the table should describe
what actually gets dispatched, not an aspiration.

## Waiting for a worker

Any turn whose only purpose is to learn whether a dispatched worker has reported counts as waiting:
re-read status, re-list agents, schedule a timer, or take a no-op turn to check again. Different
routing work is not waiting.

Arm a duration-bearing background wait whose command exits when about 5 minutes elapse, and whose
exit notifies the orchestrator. Use `Monitor` on that command, or a backgrounded Bash `until`-loop
with `sleep`; do not use `Monitor.timeout_ms` for cadence because it
kills the monitor instead of blocking the caller. End the turn and let the notification or report
wake the orchestrator. Do not spend a turn spinning or check before a notification arrives.

Leave about 5 minutes between checks. Cap at 3 check turns or about 20 minutes total per dispatch,
whichever comes first — then inspect the evidence, surface any ambiguity, and let the user decide.
Do not reset either ceiling for a partial signal, sibling progress, or a child orchestrator saying
it is still working. Do not use back-to-back checks or invent another mechanism.

Never ping a child observed as live and still working to ask whether it is done. Absence of a
report and elapsed time alone do not show that the child stopped; use observed child status, never
impatience, as the discriminator.

When you dispatch a child and observe it stopped or completed without delivering its result, send
one direct `SendMessage` telling it to resume from its transcript and deliver the report. This is
not a re-dispatch, not a re-run of the assignment, and not a ping of a live worker. If it stops
silently a second time, perform the ordered artifact-and-status check below, then stop and surface.
Do not re-dispatch the assignment over work that already survives in its phase worktree.

If you receive a report evidently intended for another agent, forward it to that agent with
`SendMessage` and record the relay in your own report. Treat a named assignment belonging to
another agent or a peer-unreachable preamble as evidence of the intended recipient. Relaying is
not polling: it delivers a result that already exists instead of asking for one.

Cross-session messaging is frequently fallible: about one report in three was lost in the observed
session after its work landed. Treat reconstruction from the surviving artifact as a normal path,
not an emergency procedure.

At dispatch time, record an assignment-specific baseline for every named on-disk output: its path
and content hash or explicit absence, repository `HEAD`, and its relevant porcelain status line.
The orchestrator performs this as the read-only repository-status read permitted by its boundary,
not as worker work. For a first dispatch, record a missing named output as absent. For a read-only
assignment with no on-disk output, record explicitly that no artifact is expected.

At the cap, inspect in this order:

1. Compare each named output with its recorded baseline. Require a post-dispatch hash change or a
   new file, and validate that the delta has the shape the assignment required.
2. Then inspect the child's status with `ListAgents`. It is confirmed available to a top-level
   orchestrator; availability to nested child orchestrators and workers is unconfirmed.

A child shown as completed while the orchestrator still waits means its report was lost, not that
its work is pending. Reconstruct completion only from both a validated post-dispatch delta and a
completed child status. Continue from the artifact and record in the flow notes that completion
was reconstructed rather than received. This is routine recovery; proceed without user escalation
when both observations validate.

Treat a byte-identical artifact, a mismatched or partial delta, or a missing baseline as no
evidence of completion regardless of child status. For an artifact-less read-only assignment,
child status is the only available signal but cannot reconstruct the missing report; stop and
surface. Where `ListAgents` is unavailable, as noted above, stop and surface any ambiguity rather
than infer completion or wait longer. Proof of completion is observed, never inferred.

Apply the cap independently at every level of a nested wait; do not extend a parent's cap because
its child orchestrator is itself waiting. Accept a late report after reconstructed completion as
confirmation; do not re-run the assignment or apply its result twice.

When stopping, do not retry the dispatch. Report the role and assignment, the completion evidence
found and missing, every partial artifact path, and the choices to resume from the artifact or
re-dispatch. Surface these choices and let the user decide.
