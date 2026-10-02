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
| `release-worker` | Version/docs/changelog preparation, push, and PR creation (the release commit is `workspace-worker`'s) | Declaring an unverified implementation ready |
| `release-verifier` | Verify release artifacts, branch safety, and PR readiness | Producing the release artifacts it verifies |

Keep reviewer roles independent from the worker whose artifact they review. A worker may be
reused across batches of the same kind, but do not use the implementer as `batch-reviewer` or
`code-reviewer`, the planner as `plan-reviewer`, or the release worker as `release-verifier`.

Native-only tags (scope: see those agent files): `discovery` ends `DISCOVERY_COMPLETE`/`DISCOVERY_PARTIAL`, `planner` `PLAN_COMPLETE`/`PLAN_PARTIAL`.

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

  An "Unknown agent" error for `trip:<role>` means a stale plugin install: retry that one
  dispatch with `general-purpose` and tell the user to run `/plugin marketplace update` and then
  `/reload-plugins`.
- `subagent:<agent-name>`: launch the named native agent instead of `trip:<role>`. It is for a
  project's pinned copy of a role's agent (see *Model and effort on the subagent harness* below);
  the copy must keep the role's contract and completion tags.
- `codex-bridge`: invoke the role mapping below. Pass model/effort as explicit per-run overrides;
  do not mutate `.codex/config.toml`.
- `skill:<name>`: invoke the named installed worker skill, including the role, artifact, scope,
  completion contract, and requested model/effort in the assignment.

### Model and effort on the subagent harness

When a role's row names a model, pass it as `model` on every dispatch, and re-read this table after
any compaction rather than recalling it. When the row is blank, the agent file decides: its
`model:` frontmatter, or — when that is absent too — the orchestrator's own model. That last
fallback is silent and expensive: one observed run lost its routing line to a compaction and sent
36 worker dispatches in a row to the orchestrator's top-tier model. So leave a row blank only when the
role's agent file sets a `model:` you accept, or running that role on the orchestrator's model is
acceptable.

The Effort column has no effect on a plain `subagent` dispatch, because the Agent tool takes no
effort field. To pin a role's effort, keep a copy of the role's agent with `model:` and `effort:`
in its frontmatter under the project's `.claude/agents/`, then route the role to it with
`subagent:<agent-name>`. Run `/reload-plugins` (or restart) so the new agent type registers.

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
4. verification expected from that worker;
5. a completion tag and a short report format — about 25 lines at most: files, counts, verdict,
   and one short entry per finding (`file:line` and the fix). No narrative, pasted diffs or logs;
   and
6. for any worker that touches a worktree, its **location check**: the absolute path and the
   literal first command `cd <path> && pwd && git rev-parse --show-toplevel && git branch
   --show-current`, with the expected output and "on any mismatch, stop and report". A dispatch
   that *creates* the worktree checks the primary checkout instead, then runs the check against
   the new path once it exists. Workers
   prefix every later command with `cd <path> &&` or use `git -C <path>`; the shell's directory
   does not reliably persist between commands, and "work in the worktree" alone has repeatedly
   sent workers — weaker models especially — into the primary checkout or a misspelled sibling
   path.

Report length is a cost, not a style choice: every report lands in the orchestrator's context and
is re-read on every later turn. Measured over one month of runs, full worker reports were the
largest single source of orchestrator context and the main driver of compactions.

Never tell a worker to invoke a `TRIP-*` skill. The phase skills are orchestrators; a worker that
loads one starts improvising orchestration (worktree tools, nested dispatch) and has hung on the
resulting permission prompt. Pass the concrete steps instead. Every worker runs in the foreground:
it keeps each command under about 8 minutes, never backgrounds a command or waits on a
notification, and on a denied or approval-pending tool call stops at once with
`BLOCKED: <command> — <reason>` and its non-success tag. A permission prompt raised inside a
background worker may never reach the user — such waits have run for 10 and 16 hours.

The orchestrator consumes reports, not hidden worker context. Carry decisions, corrections, and
open findings explicitly into every subsequent assignment. Dispatch independent roles in
parallel when the harness permits it; serialize roles that consume one another's artifacts.
Independent roles explicitly include independent implementation phases: dispatch one isolated
batch loop per phase in the current dependency frontier, in parallel when the harness permits it.

### Lanes

A **lane** is one worker's exclusive set of writable paths for one dispatch. Isolation in TRIP
comes from two mechanisms at different scales: a worktree isolates a *phase*, and a lane isolates a
*worker* inside a worktree. Two workers running at once in one worktree share a working tree and a
git index, so the worktree grants them nothing — only lanes do.

Whenever a dispatch joins a worktree that already has a live worker, give each a lane: state its
paths as contract item 3, name the sibling's paths as the sibling's, and confirm the two sets are
disjoint. The common case is a `planner` amending the plan document beside an `implementer`
writing code; lanes make that safe, with the planner's lane being the plan file alone. Where the
sets would overlap, serialize the dispatches instead — lanes are the licence for concurrency, so
no lane means no concurrency.

Inside a lane a worker writes its own paths, reads anything, and scopes every formatter and linter
run to its own files. The git index sits outside every lane: it belongs to `workspace-worker`,
dispatched alone. Those two boundaries carry the whole rule, because each failure they prevent is
silent — a tree-wide formatter rewrites files a sibling holds mid-edit, `git add -A` sweeps a
sibling's half-finished work into a commit, and two workers on one file overwrite each other. None
surfaces as an error; all three surface later as a defect nobody can trace.

### Destructive git

**Destructive git** is the command class that discards uncommitted work: `git stash`, `git
checkout -- <path>`, `git restore`, `git reset --hard`, `git clean`. No role runs them — worker or
orchestrator, assignment naming one or not. TRIP earns this hard guardrail: projects on this
workflow may defer committing until release, so the working tree routinely holds the only copy of
every batch landed so far, and one such command ends the flow's work with no recovery path.

The positive target, and the reason the ban costs nothing: **rewrite forward**. A worker reaching
for destructive git is nearly always undoing its own edit, and the way to undo an edit is to write
the intended content again. That reaches the same end state, leaves every sibling's work intact,
and is what the report can then describe. Where a worker judges that the tree itself must be
reset, it reports that with its blocked tag and stops, leaving the decision to the user — a
worker's judgment that the work at risk is worthless has been wrong before, and the loss is
silent.

### Clean-tree check

Several steps require a worktree to hold no unreported work. The **clean-tree check** is:

- **after a commit**: `git -C <wt> status --porcelain -- . ':!.codex-bridge'` prints nothing;
- **before a commit**, when staged entries are expected: `git -C <wt> diff --name-only -- .
  ':!.codex-bridge'` and `git -C <wt> ls-files -o --exclude-standard -- . ':!.codex-bridge'` both
  print nothing.

`.codex-bridge/` is excluded because `codex-bridge` keeps its state in the worktree it runs in;
projects should also gitignore it (`TRIP-init` Phase 6). Any other entry is either work nobody
reported or a file some run rewrote. Surface it rather than sweeping it in with `git add -A`.

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

At dispatch time, record an assignment-specific baseline for every named on-disk output: its path
and content hash or explicit absence, repository `HEAD`, and its relevant porcelain status line.
The orchestrator performs this as the read-only repository-status read permitted by its boundary,
not as worker work. For a first dispatch, record a missing named output as absent. For a read-only
assignment with no on-disk output, record explicitly that no artifact is expected.

Any turn whose only purpose is to learn whether a dispatched worker has reported counts as waiting:
re-read status, re-list agents, schedule a timer, or take a no-op turn to check again. Different
routing work is not waiting. **Every waiting turn re-reads the orchestrator's whole context**, so
waiting turns are the most expensive thing an orchestrator does. One observed run made 1,613 no-op
`true` calls and spent 2.9 B input tokens doing nothing else.

A background worker's completion notification is the primary wake signal; you do not need to poll
for it. Waiting therefore means:

- **End the turn.** Never call a tool only to pass time or check status: no `true`/`:` no-ops, no
  foreground `sleep` or `until` loops, no `ListAgents` or status reads on a timer, and no blocking
  output read for a worker whose notification will arrive anyway.
- **One watchdog per flow, not per dispatch.** While at least one worker is in flight, keep exactly
  one background wait armed — a `Monitor` on, or backgrounded Bash `until`-loop around, a command
  that exits after about 15 minutes. Do not use `Monitor.timeout_ms` for cadence; it kills the
  monitor instead of blocking the caller. When it fires and a worker is still in flight, check
  once and re-arm it. Do not arm a second one beside it. When nothing is in flight, stop it.
  Ignore a stale watchdog firing that predates a report you have already handled; do not answer
  it with a turn of its own.
- **Never end a turn idle.** Before ending a turn while the flow still has work, confirm that a
  worker is in flight with the watchdog armed, or that you are asking the user a question. Ending a
  turn with remaining phases and nothing in flight stalls the run silently until the user notices —
  observed as a phase committed and the next one never dispatched, found 7 hours later.

**Stuck means inactive, not slow.** Elapsed time is not evidence: healthy implementer and
test-worker dispatches commonly run 40+ minutes (p90 of ~44 minutes measured). When the watchdog
fires, check each in-flight worker's last activity, a read-only status read. For a native
subagent, that is the modification time of the output file the Agent tool returned at dispatch,
or of its transcript under `~/.claude/projects/<project>/<session>/subagents/`. For
`codex-bridge`, it is the job's state from `/codex:status`. A worker with no new activity for about 15 minutes is stalled, most likely on a
permission prompt the user cannot see. Inspect the evidence below and surface the stall to the
user at once, naming the role and the last command it ran. A worker that is still active is
working; leave it alone. Do not reset the inactivity window for a partial signal, sibling progress,
or a child orchestrator saying it is still working.

Never ping a child observed as live and still working to ask whether it is done. Absence of a
report and elapsed time alone do not show that the child stopped; use observed child status, never
impatience, as the discriminator.

When you dispatch a child and observe it stopped or completed without delivering its result, send
one direct `SendMessage` telling it to resume from its transcript and deliver the report. If it
stops silently a second time, perform the ordered artifact-and-status check below, then stop and
surface. Do not re-dispatch the assignment over work that already survives in its phase worktree.

If you receive a report evidently intended for another agent, forward it to that agent with
`SendMessage` and record the relay in your own report. Treat a named assignment belonging to
another agent or a peer-unreachable preamble as evidence of the intended recipient.

Cross-session messaging is frequently fallible: about one report in three was lost in the observed
session after its work landed. Treat reconstruction from the surviving artifact as a normal path,
not an emergency procedure.

When a worker is stalled (inactive, as defined above), inspect in this order:

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

Apply the inactivity test independently at every level of a nested wait; a child orchestrator that
is itself waiting is not activity on the parent's behalf. Accept a late report after reconstructed completion as
confirmation; do not re-run the assignment or apply its result twice.

When stopping, do not retry the dispatch. Report the role and assignment, the completion evidence
found and missing, every partial artifact path, and the choices to resume from the artifact or
re-dispatch. Surface these choices; the user picks one.

## Talking to the user

The user often reads these messages on a phone, between other work, hours after they were written.
Write every question and status update for that reader:

- **Plain language, consequence first.** Say what happens under each option before explaining why.
  No internal labels — phase or batch numbers, decision IDs, requirement codes, shorthand such as
  "bank it" — without a plain gloss next to them, and name source documents by filename.
- **Status replies are status.** When asked how a run is going, give phase and batch progress,
  what is running now, and blockers. Do not end with "keep going or pause?": the run continues
  unless the user says stop.
- **Don't re-ask a decision just made.** The user's latest instruction overrides the plan, a
  handover brief, and earlier answers. When the user has just authorized a step — invoked the skill
  that performs it, or said "do it" — skip that step's built-in confirmation.
- **Recommend the request's goal.** A recommended option must never quietly drop the request's
  primary objective; if that objective is infeasible, say so plainly as its own point.
