---
name: TRIP-init
description: Initialize the TRIP workflow in a project — creates the docs structure, the TRIP profile, and the architecture wiki
disable-model-invocation: true
argument-hint: "name of the project to initialize"
---

# TRIP Initialization Mode

You are now in **initialization mode** for setting up the TRIP workflow.

## What is TRIP?

TRIP is a structured development workflow with four phases:

- **P**lan — design features before implementation
- **I**mplement — build with proper documentation
- **R**eview — systematic code review
- **T**est — comprehensive testing

Why call it TRIP instead of PIRT? Because why not.

## What init produces

Everything TRIP knows about a project lives in the **project**, never in the skills:

| Artifact | Purpose |
| :--- | :--- |
| `docs/TRIP.md` | The **profile** — commands, version file, week anchor, project-specific guidance. Every TRIP skill reads it. |
| `docs/archi/` | The architecture **wiki** — atomic linked pages, built by `/wiki-init` |
| `docs/3-code-review/checklist.md` | Review criteria, tailored to this codebase |
| `docs/3-code-review/cr-template.md` | Code-review output skeleton |
| `docs/2-changelog/changelog_table.md` | Version tracking |
| `docs/4-unit-tests/TESTING.md` | Testing guidelines |

> **The skills are never edited.** TRIP ships as an installed plugin whose files live in a
> read-only cache. Earlier versions of this skill rewrote `SKILL.md` files in place to bake in
> project specifics; that is no longer possible, and no longer necessary. The profile is the
> single place project specifics live — which also means a plugin update never clobbers them.

---

## Your Task

Initialize the TRIP workflow for the project: **$ARGUMENTS**

If no project name was provided, ask for it before proceeding.

---

## Phase 1: Create the documentation structure

```
docs/
├── 1-plans/              # Feature planning documents
├── 2-changelog/          # Version changelog files
├── 3-code-review/        # Code review documentation
├── 4-unit-tests/         # Unit testing documentation
└── 6-memo/               # Miscellaneous notes and memos
```

`docs/5-tuto/` is created in Phase 4 only if the user wants tutorials. `docs/archi/` is created
in Phase 3 by `/wiki-init`.

---

## Phase 2: Explore the codebase

A thorough exploration — everything later phases decide depends on it. Prefer the
code-review-graph MCP tools where they cover the ground:

- `list_graph_stats` / `get_architecture_overview` / `list_communities` — structure and major modules
- `get_hub_nodes_tool` / `get_bridge_nodes_tool` — central components

Fall back to manual exploration when the graph is empty (new or unindexed project).

### Signals to identify

**Build/package files** → language: `package.json` (Node), `Cargo.toml` (Rust),
`pyproject.toml`/`setup.py`/`requirements.txt` (Python), `go.mod` (Go), `pom.xml`/`build.gradle`
(Java), `*.csproj`/`*.sln` (.NET), `CMakeLists.txt`/`Makefile` (C/C++), `platformio.ini`/`*.ino`
(embedded).

**Framework indicators** → `next.config.*`/`nuxt.config.*` (web frontend), `electron.*`/
`tauri.conf.*` (desktop), `Dockerfile`/`docker-compose.*` (containerized), `serverless.yml`/
`firebase.json` (cloud functions), `startup.s`/`linker.ld` (firmware).

**Source structure** → `src/components/` (component UI), `src/routes/`/`src/pages/` (web
routing), `src/hal/`/`src/drivers/` (hardware abstraction), `cmd/` (CLI), `lib/`/`crates/`
(libraries).

### Gather

- **Current version** — from the version file, git tags, or `__version__`. Note the format
  (SemVer, CalVer, custom). Nothing found → start at `0.1.0`.
- **Version file location** — the file a release must edit.
- **Main branch name** — `git symbolic-ref refs/remotes/origin/HEAD` or `git branch --show-current`.
- **Languages, toolchain, dependencies**
- **The actual lint / typecheck / test / build commands** — read the scripts block, Makefile,
  or CI workflow. Do not guess: a wrong command here breaks every testing gate from now on.
- **Test framework, layout and naming conventions**
- **Integration/E2E tooling**, if any

### Classify

| Type | Indicators | Key concerns |
| :--- | :--- | :--- |
| Web Frontend | React/Vue/Angular/Svelte, components, routing | Components, state, styling, routing, API calls |
| Web Backend | Express/FastAPI/Gin/Spring, routes, middleware | Endpoints, database, auth, middleware, errors |
| Full-Stack Web | Both, in a monorepo | All of the above, plus API contracts |
| Desktop App | Electron/Tauri/Qt/GTK | Windows, native APIs, IPC, cross-platform |
| Mobile App | React Native/Flutter/Swift/Kotlin | Screens, navigation, platform APIs, offline |
| CLI Tool | Main entry, arg parsing, no GUI | Commands, config, I/O, exit codes |
| Library/SDK | Public API, exports, no main entry | API surface, versioning, docs, compatibility |
| Embedded/Firmware | HAL, interrupts, memory-mapped I/O | Hardware, memory, real-time, peripherals, boot |
| Game | Game loop, rendering, entities | Loop, rendering, physics, input, assets |
| Data/ML Pipeline | Notebooks, data processing, models | Data flow, training, inference, pipelines |

Note the primary type, any secondary aspects (a CLI that is also a library), and
domain-specific concerns (real-time constraints, regulatory requirements).

---

## Phase 3: Build the architecture wiki

Invoke the `wiki-init` skill. It creates `docs/archi/` — `index.md`, `SCHEMA.md`, one page per
subsystem, and the first log entry — from the exploration you just did.

If the project already has a monolithic `docs/ARCHI.md` from an older TRIP setup, invoke
`wiki-migrate` instead: it splits the existing document into pages without losing content.

`wiki-init` ends by asking the user to approve the taxonomy. **Do not continue past this phase
until they have.** The wiki is what every later phase is written against.

If `trip-wiki` is not installed, say so and offer the fallback: generate a single
`docs/ARCHI.md` covering the sections appropriate to the project type from Phase 2, and record
in the profile that the project is un-migrated. Every TRIP skill still works — it just reads the
monolith, and pays the size cost the wiki exists to avoid.

---

## Phase 4: Write `docs/TRIP.md`

The profile. Generate it from Phase 2, in **this project's** vocabulary — a CLI tool has
commands, not routes; firmware has peripherals, not components.

````markdown
# TRIP profile — <project name>

Written by `/TRIP-init` on <date>. Every TRIP skill reads this file. Edit it freely; it is
yours, and no plugin update will touch it.

## Project

- **Name**: <name>
- **Type**: <primary type> (<secondary aspects>)
- **Main branch**: <branch>
- **Version file**: <path> (<format, e.g. SemVer>)
- **Current version**: <x.y.z>
- **Week anchor**: <YYYY-MM-DD — the Monday of the week init ran; week 1 of the project>
- **Architecture**: `docs/archi/` (wiki) | `docs/ARCHI.md` (un-migrated)

## Commands

| Purpose | Command |
| :--- | :--- |
| lint | `<...>` |
| typecheck | `<...>` |
| test:all | `<...>` |
| test:specific | `<...>` |
| test:coverage | `<...>` |
| build | `<...>` |

Omit any row the project genuinely does not have — an absent row is honest, a placeholder
is a trap.

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

## Integration checks

<When does a change need integration/E2E verification, and with what? e.g. "selectors
changed → run the E2E suite"; "API contract changed → exercise it against the local
emulator". Docs-only changes skip this. Write "None" if the project has no such tooling.>

## Plan considerations

<The bullets TRIP-1-plan applies to every plan, for THIS codebase. Drop what does not
apply; add what is unique. Examples by type:
  web frontend — performance (memoisation, lazy loading), accessibility, responsive
    breakpoints, empty/loading/error states, theming
  web backend  — schema changes and migrations, API versioning and compatibility,
    input validation, authz, rate limits, partial failures
  CLI          — help text, config precedence (flags > env > file > default), exit
    codes, cross-platform path and shell handling
  embedded     — stack and heap impact, interrupt latency, power budget, pin and
    peripheral conflicts, startup races and watchdog
  library      — public API surface, breaking changes and deprecation policy, thread
    safety, error propagation>

## Guidance sections

<Per-component-type analysis checklists for TRIP-1-plan, derived from the wiki's page
taxonomy. One section per major component type this project actually has — "For new
peripheral drivers", "For new commands", "For new API endpoints" — each listing what a
plan must work out before implementation starts.>

## Test structure

<Where tests live, file naming, how they are discovered.>

## Test priorities

<What matters most to test here, by test type, and what to test about it.>

## Tutorials

- **Enabled**: <yes|no>
- **Level**: <beginner|intermediate|advanced>
- **Focus**: <what the user wants to learn>
- **Style**: <concise|balanced|verbose>

## Custom plan sections

<Any extra sections the user wants in every plan. "None" if there are none.>
````

### Ask the user what only they can answer

One `AskUserQuestion` call, several questions:

1. **Tutorials** (header "Tutorials"): "Generate a tutorial after each release?" — "Yes" / "No".
   If yes, follow up for level, focus (multi-select) and style, and create `docs/5-tuto/`.
2. **Custom plan sections** (header "Plan"): "Any project-specific sections you want in every
   plan?" — "No custom sections" / "Yes, add custom sections".

Everything else you derive from Phase 2 — do not ask the user for facts you can read out of the
repository.

### Week anchor

```bash
date -d "last monday" '+%Y-%m-%d'   # if today is Monday, use: date '+%Y-%m-%d'
```

The week init runs is week 1. `TRIP-3-release` counts elapsed weeks from this fixed date, so it
works across year boundaries indefinitely.

---

## Phase 5: Install the project-local review files

Copy the templates out of the plugin into the project, then tailor them:

```bash
mkdir -p docs/3-code-review
cp "${CLAUDE_PLUGIN_ROOT}/templates/checklist.md"   docs/3-code-review/checklist.md
cp "${CLAUDE_PLUGIN_ROOT}/templates/cr-template.md" docs/3-code-review/cr-template.md
```

They must be project-local: they are the single source of truth for review criteria, they get
tailored per project, and the plugin's own copy is read-only.

**Tailor `checklist.md`** — replace the marked block with the checklist sections that matter for
*this* codebase, derived from the wiki. Examples: a web backend gets input validation, consistent
error shape, correct status codes, API versioning, rate limiting; firmware gets stack usage, DMA
alignment, peripheral release, power modes, watchdog, race conditions; a CLI gets help-text
clarity, actionable errors, exit codes, progress feedback. Sharpen the generic sections too, and
delete any that do not apply.

**Tailor `cr-template.md`** — its Checklist section must list the *actual* section names from the
checklist you just wrote.

**Update the approval gate** at the bottom of `checklist.md` with the real commands from the
profile.

---

## Phase 6: Create the supporting files

### `docs/2-changelog/changelog_table.md`

First entry is the current version with the patch bumped (`1.2.3` → `1.2.4`; nothing found →
`0.1.0`).

```markdown
# Changelog Table

| Version   | Week | Commit Message                  |
| --------- | ---- | ------------------------------- |
| `X.Y.Z+1` | 1    | chore: initialize TRIP workflow |

# Changelog Summary

- **vX.Y.Z+1 (TRIP Initialization — Week 1, DD-MM-YYYY)**:
  - **Setup**: initialized TRIP workflow with docs structure
  - **Documentation**: built the architecture wiki at `docs/archi/` (<N> pages)
  - **Files added**: docs/TRIP.md, docs/archi/, docs/3-code-review/{checklist,cr-template}.md, docs/4-unit-tests/TESTING.md
```

New entries go at the **top** of each section.

### `docs/4-unit-tests/TESTING.md`

Framework, the real commands, test organisation, the conventions actually observed in the
codebase, and coverage requirements — or "Not defined". Do not invent a threshold.

---

## Post-initialization checklist

- [ ] `docs/` folders created: 1-plans, 2-changelog, 3-code-review, 4-unit-tests, 6-memo
- [ ] Codebase explored; version, version file, main branch and real commands identified
- [ ] Project type classified
- [ ] `docs/archi/` built by `/wiki-init` (or `/wiki-migrate`) **and approved by the user**
- [ ] `docs/TRIP.md` written, with no `<placeholder>` left unfilled
- [ ] Tutorial preference recorded (and `docs/5-tuto/` created if enabled)
- [ ] `docs/3-code-review/checklist.md` installed and tailored
- [ ] `docs/3-code-review/cr-template.md` installed, section names matching the checklist
- [ ] `docs/2-changelog/changelog_table.md` initialized
- [ ] `docs/4-unit-tests/TESTING.md` written against the actual test setup
- [ ] No TRIP skill file was edited — they are read-only, and the profile replaced the need

---

## Notes for the agent

- **Explore before classifying.** Read key files; do not infer the project type from directory
  names alone.
- **Verify the commands.** Run them where it is safe to. A profile with a wrong test command
  poisons every gate downstream.
- **Use the project's terminology** in the profile and the wiki.
- **Document what exists**, not an idealised version of it.
- **User approval of the wiki is mandatory** — never skip it, and iterate if they ask for changes.
