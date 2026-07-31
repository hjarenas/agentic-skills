---
name: wiki-init
description: Create the docs/archi/ architecture wiki for a project and write its SCHEMA.md conventions file
disable-model-invocation: true
argument-hint: "[project name]"
---

# Wiki Init

Create a fresh architecture wiki at `docs/archi/`. For a project that already has a
`docs/ARCHI.md`, use `/wiki-migrate` instead — it calls this skill and then splits the existing
document into pages rather than starting empty.

Read [`../../references/wiki-spec.md`](../../references/wiki-spec.md) first. It defines the
layout, page format, linking rules and branch-safety conventions this skill implements.

## Step 1 — refuse to clobber

If `docs/archi/` already exists, stop and report what is there. Never overwrite an existing
wiki; the user wants `/wiki-lint` or `/wiki-ingest`, not init.

If `docs/ARCHI.md` exists, stop and point at `/wiki-migrate`. Initialising over a monolith
would strand its content.

## Step 2 — explore the codebase

Work out what the project is before writing conventions for it. Prefer the code-review-graph
MCP tools if they are available and the graph is populated:

- `get_architecture_overview` / `list_communities` — major modules and their groupings
- `get_hub_nodes_tool` / `get_bridge_nodes_tool` — the components everything depends on

Fall back to reading build files (`package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`,
`*.csproj`, `CMakeLists.txt`), entry points, and the directory structure.

Determine: the project's type (web frontend/backend, CLI, library, embedded, mobile, data
pipeline, game), its language and toolchain, its current version, and the four to eight
subsystems a newcomer would need explained.

## Step 3 — create the structure

```
docs/archi/
├── index.md
├── SCHEMA.md
├── pages/
└── log/
```

## Step 4 — write SCHEMA.md

`SCHEMA.md` is the project-specific contract every other wiki skill reads. Generate it from
what you found in Step 2 — the section below is the shape, not the content:

```markdown
# Wiki conventions for <project>

## What this wiki covers
<one paragraph: the architecture of <project>, a <type> written in <language>>

## Page taxonomy
<the page groups for THIS project, with what belongs in each. A CLI tool gets
 Commands / Configuration / IO; a web backend gets Runtime / Data / Auth /
 Integrations; embedded gets Peripherals / Memory / Timing / Boot. Use the
 project's own vocabulary — peripherals, not components; commands, not routes.>

## Naming
- Page slugs: kebab-case, noun-phrase, no version numbers in the name
- <any project-specific naming rules>

## Size limit
A page over <N> lines must be split. <Default 400. Lower it for terse codebases.>

## Code citation
Claims about behaviour cite `path/to/file.ext:line`. Paths are repo-relative.

## What does NOT go in the wiki
- Implementation detail that the code states more precisely
- Anything that changes every release (version numbers, dependency pins)
- Task-tracking, plans, changelogs — those live in docs/1-plans and docs/2-changelog
```

## Step 5 — seed the first pages

Write one page per subsystem identified in Step 2. Do not write a page you cannot ground in
code you actually read — an empty stub is worse than an absent page, because lint will not
flag it as missing.

Start each page from the template in `wiki-spec.md`: frontmatter with `status: current`,
today's date, the current project version in `verified-at`, and `links:` to the pages it
relates to.

## Step 6 — write index.md

One line per page, grouped by the taxonomy from `SCHEMA.md`, **sorted by slug within each
group**. That sort is what lets two branches add pages without conflicting — see
`wiki-spec.md` §Branch safety.

## Step 7 — write the first log entry

`docs/archi/log/v<current-version>.md`:

```markdown
# v<x.y.z>

## <today> — wiki initialised

Created the architecture wiki from a survey of the codebase at <short-sha>.

Pages added: <slug>, <slug>, …
```

## Step 8 — hand back

Report to the user: the taxonomy chosen, the pages written, and anything you deliberately did
not document because you could not ground it. Then use `AskUserQuestion`:

- **Question**: "The wiki is seeded with N pages. How does the taxonomy look?"
- **Options**: "Looks good" · "Regroup the pages" · "Missing a subsystem"

Do not proceed to ingest or lint until the user has looked.
