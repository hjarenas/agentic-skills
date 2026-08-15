# Wiki conventions for agentic-skills

## What this wiki covers

The architecture of `agentic-skills`: a Claude Code **plugin marketplace** — a git repo of
installable plugins, each a bundle of `SKILL.md` files (prompt-engineered instructions, mostly
Markdown) plus a thin layer of Python scripts where behavior needs to be mechanically reliable
rather than model-interpreted. There is no application runtime here; "the code" is prompts, and
"correctness" is largely about frontmatter contracts, cross-references between skills, and
per-plugin semver discipline.

## Page taxonomy

- **Distribution** — how the repo ships itself: the marketplace/plugin manifest structure, and
  how `pocock-core` mirrors upstream content without becoming a stale fork.
- **Plugins** — one page per plugin: what it does, its skills, and how they relate to each other.
  A newcomer reads the Distribution page once, then the one or two Plugin pages relevant to
  whatever they're touching.
- **Mechanisms** — a cross-cutting behavior that spans more than one plugin and would otherwise
  bloat every plugin page it touches (e.g. [[worktree-parallelism]], which spans `trip`'s flow
  orchestration and `codex-bridge`'s workspace allowlist). Reserve this category for genuinely
  cross-plugin mechanics; a single-plugin feature belongs in that plugin's own page instead.

Five plugins currently exist (`trip`, `trip-wiki`, `codex-bridge`, `pocock-core`, `toolbox`) —
five Plugin pages, one Distribution page. A sixth plugin gets a sixth page; retiring one deletes
its page (mark `status: superseded` first if something replaces it).

## Naming

- Page slugs: kebab-case, noun-phrase, no version numbers in the name (e.g. `trip-plugin`, not
  `trip-1.3`)
- A page about plugin `<name>` is slugged `<name>-plugin` to avoid colliding with that plugin's
  own directory name in casual cross-reference

## Size limit

A page over **300 lines** must be split. Lower than the spec's 400-line default because these
pages describe prompt content, not code — a 300-line page is already describing several
skills' worth of behavior in detail.

## Code citation

Claims about behavior cite `path/to/file.ext:line` for Python scripts, or `path/to/SKILL.md`
(no line number — skill prose shifts too easily for line citations to stay meaningful; name the
section heading instead when precision matters) for skill content. Paths are repo-relative.

## What does NOT go in the wiki

- The content of individual `SKILL.md` files — the wiki describes what a plugin does and how its
  pieces fit together, not a restatement of each skill's own instructions. Read the skill for that.
- Per-plugin version numbers — they change every release; cite `plugins/<name>/.claude-plugin/plugin.json`
  instead of a number that will be stale by the next ingest.
- Anything `docs/TRIP.md` already owns: commands, agent routing, plan/testing conventions for
  *using* TRIP in a downstream project. This wiki is about how `agentic-skills` itself is built.
