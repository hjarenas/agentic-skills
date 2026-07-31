# Inspirations

What this marketplace borrowed, from whom, and why. Where something was taken and then changed,
the change and its reason are stated — the interesting part is usually the divergence.

---

## PiLastDigit — the TRIP workflow

- **Source**: [github.com/PiLastDigit/TRIP-workflow](https://github.com/PiLastDigit/TRIP-workflow) (MIT)
- **Used in**: `trip` (the entire plugin — this is where TRIP comes from)
- **Taken**: the workflow itself. The three numbered skills `/TRIP-1-plan`, `/TRIP-2-implement`,
  `/TRIP-3-release`; the supporting cast `/TRIP-init`, `/TRIP-upgrade`, `/TRIP-hotfix`,
  `/TRIP-research`, `/TRIP-compact`; the numbered `docs/` structure (`1-plans/`, `2-changelog/`,
  `3-code-review/`, `4-unit-tests/`, `5-tuto/`, `6-memo/`); `ARCHI.md` as persistent
  architectural context; the week-numbered, SemVer-tagged release ceremony with its changelog
  table and code-review promotion; and the name, including the joke about why it is TRIP and not
  PIRT.

**Why**: it solves the problem that actually matters for agent-assisted work — an agent starting
cold every session, re-deriving the architecture and inventing conventions the project already
has. Its stated design goal is minimalism: *"3 numbered skills. 1 architecture file. 0 PhD
required."* That restraint is why it was worth building on rather than replacing; most of what
follows is adaptation, not disagreement.

**Changed**:

- **`ARCHI.md` became a wiki.** The one thing that did not scale here. It is the "central nervous
  system" by design, so every skill reads it in full — which is fine until it is 20k tokens, and
  `/TRIP-compact` exists precisely because it gets there. See the Karpathy section below for what
  replaced it; `/TRIP-compact` is kept, deprecated, for projects that have not migrated.
- **Distribution moved from copy-in to plugin.** Upstream installs by copying `skills/` into
  `.claude/skills/` and then customizing those copies in place — `/TRIP-init` literally rewrites
  its sibling `SKILL.md` files to bake in test commands, version file and checklist sections. A
  plugin cache is read-only, so that is no longer possible; project specifics moved to
  `docs/TRIP.md`. This also retires the reason `/TRIP-upgrade` existed (reconciling a new skeleton
  against local edits), so it was repurposed into a one-time migration onto the profile.
- **Release ends in a pull request, not a push to the main branch.** Upstream's step 10 commits,
  tags and pushes; here the release lands on a feature branch, opens a PR with a description
  written so the reviewer need not read every file, and tags after the merge.
- **Codex became a first-class gate**, not a variant. Upstream ships "Codex-specific variants" of
  the skills; here `codex-plan-review` and `codex-code-review` are iterative loops with three-state
  verdicts that TRIP-1 and TRIP-2 branch on, living in their own plugin so they can be used
  without TRIP.
- **Added `/TRIP-auto`** for unattended runs, and `/TRIP-test` and `/TRIP-review` as explicit
  standalone phases.

**A note on `/TRIP-auto`**: it is not a wrapper that calls `/TRIP-1-plan`, `/TRIP-2-implement` and
`/TRIP-3-release` in sequence. It restates a **compressed copy** of each phase inline, with its
own autonomy rules (exactly two user interactions), its own PR-description template, and its own
failure handling. That duplication is deliberate — an autonomous run needs different defaults, not
the same steps with the questions suppressed — but it is duplication, and it drifts: the wiki
migration had to be applied to it separately from the skills it mirrors. Treat it as a fourth
place to edit whenever the phase mechanics change.

---

## Andrej Karpathy — the LLM Wiki

- **Source**: [gist: LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- **Used in**: `trip-wiki` (the whole plugin)
- **Taken**: the pattern. Three layers — immutable raw sources, an LLM-maintained wiki of
  markdown pages, and a schema file that states the conventions — plus the operating loop of
  **ingest → query → lint**, an `index.md` catalog read first, and an append-only `log.md`.

**Why**: TRIP kept its architecture in one `docs/ARCHI.md` that every plan, review and
implementation read in full. It grew without bound, cost the whole file to read even for a
one-subsystem change, and conflicted on every merge because every branch edited it. `TRIP-compact`
fought the symptom by *deleting detail* — trading accuracy for size, permanently. The LLM Wiki
inverts that: knowledge is compiled once and kept current, and pages are **split** rather than
compressed, so growth costs more files instead of less truth.

**Changed**:

- **The wiki is the project's, not a personal one.** It lives in `docs/archi/` inside the repo
  and describes the code beside it, so it is versioned with that code and a branch's wiki
  describes that branch's architecture.
- **`log.md` became `log/v<x.y.z>.md`, one file per release.** A single append-only log is a
  merge-conflict magnet — every branch appends to the same last line. Per-release files mean
  branches heading for different versions never touch the same file.
- **`index.md` is one sorted line per page**, so two branches each adding a page merge without
  help. Karpathy's index is free-form; ours trades a little expressiveness for mechanical
  mergeability.
- **Claims cite `file:line`.** A project wiki can be checked against the code it describes,
  which a wiki of external sources cannot. Lint uses this to catch stale references.
- **Lint is half script, half model.** `wiki_lint.py` settles the mechanical questions — broken
  links, orphans, index coverage, size, dead code references — so the model spends its attention
  on contradictions and stale claims, which are the checks that actually need judgement.

---

## Matt Pocock — Skills for Real Engineers

- **Source**: [github.com/mattpocock/skills](https://github.com/mattpocock/skills) (MIT)
- **Used in**: `pocock-core`
- **Taken**: eight skills — `grill-with-docs`, `to-spec`, `to-tickets`, `triage`, `teach`,
  `writing-great-skills`, `research`, `wayfinder` — plus three they depend on: `grilling`,
  `domain-modeling`, and `setup-matt-pocock-skills`.

**Why**: TRIP is strong from an agreed plan onward and weak before it. `TRIP-1-plan` asks a few
`AskUserQuestion` rounds and then writes the plan — fine when the shape of the work is already
known, thin when it is not. Pocock's front end fills exactly that gap: `grilling` interviews one
question at a time until the thinking holds, `to-spec` synthesises without re-interviewing,
`to-tickets` cuts tracer-bullet slices, and `wayfinder` handles work too large for one session.
`writing-great-skills` is the reference the skills in this repo are written against — its
distinction between model-invoked and user-invoked skills, and its framing of predictability as
*process* rather than output, shaped the frontmatter choices throughout.

**Vendored rather than subscribed**, deliberately. His plugin (`/plugin install
mattpocock-skills`) is the better choice for most people: always current, zero maintenance. But
read-only skills cannot be wired into TRIP, and the point here is to wire them in. The cost of
forking is drift, so `UPSTREAM.json` pins the commit each file came from and
`scripts/vendor-sync.py` uses that pin as a **merge base** for a real 3-way merge — untouched
files fast-forward, edited files merge, and only genuinely overlapping edits conflict.

**Also taken**: the philosophy in his README — *small, composable, hackable skills over one big
framework that owns your process*. This marketplace is five focused plugins rather than one
monolith for the same reason.

---

## OpenAI — the Codex plugin for Claude Code

- **Source**: [github.com/openai/codex-plugin-cc](https://github.com/openai/codex-plugin-cc) (Apache-2.0)
- **Used in**: `codex-bridge` (declared dependency), and `/codex:adversarial-review` as an extra gate
- **Taken**: the runtime. `codex-companion.mjs` handles job tracking, background execution,
  `/codex:status`, `/codex:result`, `/codex:cancel`, and auth checks.

**Why**: the previous setup drove `codex exec --json` through five bash scripts with a `jq`
dependency and hand-rolled per-target thread files. All of that is bookkeeping the plugin already
does, better, and updates on its own.

**Not taken: the prompts.** `/codex:review` and `/codex:adversarial-review` ship OpenAI's own
prompts and emit a two-state verdict. They are good, and worth running — but they are **git-diff
scoped**, so they cannot review a markdown plan at all, they read the diff cold without the
project's architecture or review checklist, and they have no counterpart to the "do not flag
this" exclusions TRIP depends on. `/codex:adversarial-review`'s prompt explicitly instructs the
opposite: *"Do not give credit for good intent, partial fixes, or likely follow-up work."*
Excellent for attacking a design, wrong for an iterative loop that must converge.

So `codex-bridge` keeps TRIP's prompt templates and feeds them to the plugin's runtime through
`codex-companion.mjs task --prompt-file`.

**Changed — reviews became stateless.** The runtime can only resume a workspace's *last* thread.
TRIP-2 alternates implement → review → implement, so `--resume-last` during a review would resume
the implementation thread. Rather than accept that, every review turn is now a fresh run and the
loop state travels in the prompt: the previous review is stored under `.codex-bridge/` and
spliced back in. This makes the implementer notes load-bearing — they are the only thing
distinguishing "I fixed it" from "I disagree, and here is why" — which is now stated wherever the
loop is documented. Only `codex-implement` uses `--resume-last`, where continuing the batch is
the point and nothing runs in between.

---

## Anthropic — the plugin and marketplace system

- **Source**: [Claude Code plugin docs](https://code.claude.com/docs/en/plugins-reference)
- **Used in**: the repository's whole shape

**Why**: distributing skills by copying them into each project meant every project held its own
customized fork, and every upgrade was a three-way reconciliation between the new skeleton and
local edits. `TRIP-upgrade` existed solely to perform that reconciliation.

**Taken**: `marketplace.json` with relative-path plugin sources, plugin `dependencies` (so `trip`
pulls `trip-wiki`), and `allowCrossMarketplaceDependenciesOn` so `codex-bridge` can depend on
OpenAI's `codex` plugin without either marketplace trusting the other implicitly.

**Consequence that reshaped TRIP**: installed plugins live in a **read-only cache**, so
`TRIP-init` can no longer rewrite its own sibling `SKILL.md` files to bake in project specifics —
which is what it used to do. Everything project-specific now lives in the *project*:
`docs/TRIP.md` for the profile, `docs/3-code-review/` for the review criteria,
`docs/archi/SCHEMA.md` for the wiki conventions. This is strictly better than the old design: a
plugin update cannot clobber customizations, because it cannot reach them. `TRIP-upgrade` was
repurposed from "reconcile two skeletons" into "migrate a legacy in-place install onto the
profile", which it does once and then never again.

---

## Considered and not used

**[AgriciDaniel/claude-obsidian](https://github.com/AgriciDaniel/claude-obsidian)** (10.1k★, MIT)
and **[eugeniughelbur/obsidian-second-brain](https://github.com/eugeniughelbur/obsidian-second-brain)**
(3.7k★, MIT) are the two popular implementations of the LLM Wiki idea, and claude-obsidian is
already a Claude Code plugin with `wiki-ingest` / `wiki-query` / `wiki-lint` skills that map
almost name-for-name onto what `trip-wiki` does.

They were not used because both are built for a **personal** second brain, and this wiki is the
code's memory:

- The vault must live **outside** the repo — resolved via `--vault`, `CLAUDE_OBSIDIAN_VAULT`, or
  the nearest `.claude-obsidian.json`, and explicitly never the product checkout. Project docs
  that live outside the project cannot be reviewed in the pull request that changes them.
- **No branch or worktree awareness anywhere** — no mention of either in the docs or skills. A
  vault outside the repo is branch-blind: notes written on a feature branch stay visible after
  you switch away, with no way to mark unmerged work.
- claude-obsidian holds a **process-lifetime vault-wide lock** and returns conflict exit 75 on
  concurrent changes, so two agents in two worktrees serialize or fail.
- Both bring machinery — a Python transaction core, sha256-approved operation plans, provenance
  ledgers — that is proportionate to a decade-long personal knowledge base and disproportionate
  to "don't let the architecture doc get huge".

Taking the pattern instead of the product cost about 700 lines of skills and one 200-line linter,
and left `docs/archi/` as plain markdown that merges like code — while staying a valid Obsidian
vault for anyone who wants the graph view.

**[mattpocock/skills as a subscribed plugin](https://github.com/mattpocock/skills)** — see above;
the right default for most people, wrong here because the skills need editing.
