---
name: TRIP-upgrade
description: Upgrade an existing TRIP project—migrate legacy customized skill copies onto the plugin model, or add missing agent-routing configuration to an existing docs/TRIP.md profile
disable-model-invocation: true
---

# TRIP Upgrade Mode

Upgrade either kind of existing TRIP project:

1. **Legacy migration** — move customized `.claude/skills/TRIP-*` copies onto the plugin model.
2. **Profile migration** — add the current agent-routing schema to an existing `docs/TRIP.md`
   created by an earlier plugin version.

Run this once per project. Afterwards, upgrading TRIP is `claude plugin update trip` and nothing
else — which is the entire point.

## The problem this solves

TRIP used to be distributed by copying its skills into a project and then rewriting them in
place: test commands, version file, week anchor, checklist sections, guidance sections, all baked
into `SKILL.md` files. Every upgrade then meant a three-way reconciliation between the new
skeleton and the local edits, which is what the old version of this skill did.

Installed plugins live in a read-only cache, so that no longer works — and no longer needs to.
The customizations move into the project once, and the skeleton stops being the user's problem.

## Prerequisites

- The `trip` plugin is installed (`/plugin install trip@hjarenas-agentic-skills`).
- The project has either `docs/TRIP.md` or `.claude/skills/TRIP-*` from an older setup.
- The working tree is clean, so the migration is a reviewable diff.

If neither source exists, the project was never initialized. Point at `/TRIP-init` and stop.

## Phase 0: Select the migration path

Inspect without modifying:

```bash
test -f docs/TRIP.md && grep -n '^## Agent routing$' docs/TRIP.md
ls -d .claude/skills/TRIP-*/ 2>/dev/null
test -f .codex/config.toml && sed -n '/^model\|^model_reasoning_effort/p' .codex/config.toml
```

Choose exactly one path:

| State | Path |
| :--- | :--- |
| Legacy skills exist | Run the full migration, including routing in Phase 3.1 |
| `docs/TRIP.md` exists and lacks `## Agent routing` | Run **Profile-only routing migration** below |
| `docs/TRIP.md` already has `## Agent routing` and no legacy skills exist | Report "already current" and stop without edits |
| Neither exists | Point at `/TRIP-init` and stop |

Never replace or normalize an existing `Agent routing` section automatically. User choices in
that table are project configuration and must be preserved byte-for-byte unless the user asks
to change them.

### Profile-only routing migration

1. Read `docs/TRIP.md` and `.codex/config.toml` if present.
2. Insert `## Agent routing` immediately after `## Commands` and its table, using the current
   table from `TRIP-init` Phase 4.
3. Keep all harness defaults unchanged. If `.codex/config.toml` contains `model` or
   `model_reasoning_effort`, copy those values into the `plan-reviewer`, `implementer`, and
   `code-reviewer` rows so the effective Codex selection becomes explicit. Do not remove or edit
   `.codex/config.toml`; other Codex use may still depend on it.
4. Verify that every required role appears exactly once and that all pre-existing
   `docs/TRIP.md` content is otherwise unchanged.
5. Show the diff and report the inherited model/effort values. Do not commit unless requested.

This path is idempotent: a second `/TRIP-upgrade` sees the section and exits without edits.
After completing it, skip Phases 1-6 and use the routing items in the post-migration checklist.

---

## Phase 1: Inventory

```bash
ls -d .claude/skills/*/ 2>/dev/null
```

Sort what you find:

| Found | Meaning |
| :--- | :--- |
| `TRIP-1-plan`, `TRIP-2-implement`, `TRIP-3-release`, `TRIP-review`, `TRIP-test` | Carry customizations — extract them |
| `TRIP-init`, `TRIP-research`, `TRIP-hotfix`, `TRIP-compact`, `TRIP-auto`, `TRIP-upgrade` | Pure workflow — nothing to extract |
| `codex-plan-review`, `codex-code-review`, `codex-implement`, `codex-ask` | Superseded by the `codex-bridge` plugin |
| Anything else | Not TRIP's — leave it entirely alone |

**Older layouts**: v1 installs used `TRIP-3-review/` and `TRIP-4-test/`, and kept the release
steps inside `TRIP-2-implement`. Treat those as the same skills under their old names.

Report the inventory, then `AskUserQuestion`: "Migrate these onto the plugin model?" —
"Yes, migrate" / "Show me what would be extracted first" / "Abort".

---

## Phase 2: Extract the customizations

Read every customized skill and pull out the project-specific values. **This is the safety net —
do not delete anything until Phase 4 confirms it all landed.**

**From `TRIP-1-plan/SKILL.md`:**
- `PROJECT_NAME` — what replaced `[PROJECT_NAME]`
- `TECHNICAL_CONSIDERATIONS` — the `## Technical Considerations` section of the plan template
- `GUIDANCE_SECTIONS` — the per-component guidance that replaced `[ADAPT_TO_PROJECT: Guidance Sections]`
- `CUSTOM_PLAN_SECTIONS` — any extra sections added to the plan template

**From `TRIP-3-release/SKILL.md`** (or `TRIP-2-implement/SKILL.md` in v1 installs):
- `VERSION_FILE`, `WEEK_ANCHOR_DATE`, `MAIN_BRANCH`
- `TUTORIAL_CONFIG` — the tutorial step with its user context, or "disabled"
- `LINT_COMMAND`, `TYPECHECK_COMMAND`, `TEST_COMMAND` — may be absent in older versions

**From `TRIP-2-implement/SKILL.md`:**
- `INTEGRATION_RULES` — whatever replaced the integration/E2E impact block

**From `TRIP-review/` (or `TRIP-3-review/`):**
- `REVIEW_CHECKLIST` — from `checklist.md`, or inline in `SKILL.md` in older versions
- `CR_TEMPLATE` — from `cr-template.md` if it exists

**From `TRIP-test/` (or `TRIP-4-test/`):**
- `TEST_COMMANDS`, `TEST_STRUCTURE`, `TESTING_PRIORITIES`

**From `codex-plan-review/scripts/_common.sh`, if present:**
- `CODEX_MODEL` / `CODEX_EFFORT` — any tuned model or effort values. These move to the Codex
  plugin's own config (`.codex/config.toml`), not to the TRIP profile.

Present the extraction to the user before writing anything:

```
Extracted:
  Project name:        <name>
  Version file:        <path>
  Week anchor:         <date>
  Main branch:         <branch>
  Commands:            lint <...> | typecheck <...> | test <...>
  Tutorials:           <enabled (level/focus/style) | disabled>
  Checklist sections:  <count> (<names>)
  Guidance sections:   <count> (<names>)
  Codex model/effort:  <values, or "defaults">
```

Anything you could not find, say so explicitly — a silently missing command becomes a broken gate.

---

## Phase 3: Write the project-local files

### 3.1 `docs/TRIP.md`

Write the profile using the template in `TRIP-init` Phase 4, filled from the extraction:

| Extracted | Profile section |
| :--- | :--- |
| `PROJECT_NAME`, `VERSION_FILE`, `WEEK_ANCHOR_DATE`, `MAIN_BRANCH` | § Project |
| `LINT_COMMAND`, `TYPECHECK_COMMAND`, `TEST_COMMAND`, `TEST_COMMANDS` | § Commands |
| `INTEGRATION_RULES` | § Integration checks |
| `TECHNICAL_CONSIDERATIONS` | § Plan considerations |
| `GUIDANCE_SECTIONS` | § Guidance sections |
| `TEST_STRUCTURE`, `TESTING_PRIORITIES` | § Test structure, § Test priorities |
| `TUTORIAL_CONFIG` | § Tutorials |
| `CUSTOM_PLAN_SECTIONS` | § Custom plan sections |

Include `## Agent routing` from the current `TRIP-init` profile template. If the extracted or
existing `.codex/config.toml` has a model/effort value, make it explicit in the
`plan-reviewer`, `implementer`, and `code-reviewer` rows while preserving the config file.

Fill § Project's **Architecture** row with `docs/ARCHI.md (un-migrated)` if the project still has
a monolith — Phase 5 offers to fix that.

Anything the extraction did not yield, derive from the repository the way `TRIP-init` Phase 2
does. Leave no `<placeholder>` behind.

### 3.2 `docs/3-code-review/`

```bash
mkdir -p docs/3-code-review
```

Write `REVIEW_CHECKLIST` to `docs/3-code-review/checklist.md` and `CR_TEMPLATE` to
`docs/3-code-review/cr-template.md`. If the old install had no template file, copy the plugin's:

```bash
cp "${CLAUDE_PLUGIN_ROOT}/templates/cr-template.md" docs/3-code-review/cr-template.md
```

and adjust its Checklist section to match the checklist's actual section names.

### 3.3 Codex settings

If the old `_common.sh` had tuned model or effort values, put them in `.codex/config.toml`:

```toml
model = "<model>"
model_reasoning_effort = "<effort>"
```

The `codex-bridge` skills read the Codex plugin's config rather than carrying their own.

---

## Phase 4: Verify before deleting

Confirm every extracted value landed:

```bash
grep -n "<" docs/TRIP.md | grep -v "^\s*$"   # any surviving <placeholder> is a miss
```

Walk the Phase 2 extraction list and tick each item off against the written files. Report the
walk to the user. **Do not proceed while anything is unaccounted for.**

---

## Phase 5: Remove the local copies

Only after Phase 4 passes, and as a **separate commit** from Phase 3 so the deletion is
reviewable on its own:

```bash
git rm -r .claude/skills/TRIP-1-plan .claude/skills/TRIP-2-implement \
          .claude/skills/TRIP-3-release .claude/skills/TRIP-review \
          .claude/skills/TRIP-test .claude/skills/TRIP-init \
          .claude/skills/TRIP-research .claude/skills/TRIP-hotfix \
          .claude/skills/TRIP-compact .claude/skills/TRIP-auto \
          .claude/skills/TRIP-upgrade
git rm -r .claude/skills/codex-plan-review .claude/skills/codex-code-review \
          .claude/skills/codex-implement .claude/skills/codex-ask
```

Adjust the list to what the inventory actually found — and never remove a skill that is not
TRIP's. Those `codex-*` directories also hold `state/` folders of cached reviews; they are
disposable, but say so rather than deleting silently.

Then add `.codex-bridge/` to `.gitignore`, since the codex skills store their reviews there now.

## Phase 6: Offer the wiki migration

The project almost certainly still has a monolithic `docs/ARCHI.md`. Offer `/wiki-migrate`, which
splits it into `docs/archi/` — and update the profile's Architecture row when it is done.

This is a separate decision from the skill migration; if the user declines, everything still
works against the monolith.

---

## Post-migration checklist

- [ ] Every customization extracted and accounted for (Phase 4 walk)
- [ ] `docs/TRIP.md` written, no `<placeholder>` remaining
- [ ] `docs/TRIP.md` has exactly one complete `Agent routing` table
- [ ] Existing routing choices preserved, or Codex model/effort inherited without deleting `.codex/config.toml`
- [ ] `docs/3-code-review/checklist.md` and `cr-template.md` in place, section names matching
- [ ] Tuned Codex model/effort moved to `.codex/config.toml`
- [ ] Local `TRIP-*` and `codex-*` skill copies removed, in their own commit
- [ ] `.codex-bridge/` added to `.gitignore`
- [ ] `/wiki-migrate` run, or explicitly declined
- [ ] A TRIP command exercised end to end to confirm the profile is actually read
