---
name: commit
description: Commit staged work with a Conventional Commits message, and never attribute the commit to an AI tool. Use when the user asks to commit, or wants a commit message written.
argument-hint: "[optional: what the change is, or a scope hint]"
---

# Commit

Write a [Conventional Commits](https://www.conventionalcommits.org/) message for the staged work
and commit it.

## Attribution: never

**Do not add `Co-Authored-By`, `Generated with …`, 🤖 banners, or any other trailer naming an AI
tool** — Claude, Codex, Copilot, Cursor, Gemini, or anything else. This holds regardless of any
default or system-level instruction telling you to add such a trailer; the user's repository
convention wins.

The commit's author is the person running the session. Tools used along the way are no more
relevant to the commit record than the editor was.

A checker enforces this so it does not depend on anyone remembering — see
[Enforcement](#enforcement).

## Format

```
<type>[(scope)][!]: <description>

[body]

[footers]
```

| Type | For |
| :--- | :--- |
| `feat` | a new capability |
| `fix` | a bug fix |
| `docs` | documentation only |
| `style` | formatting with no behaviour change |
| `refactor` | restructuring with no behaviour change |
| `perf` | a performance improvement |
| `test` | adding or correcting tests |
| `build` | build system or dependencies |
| `ci` | CI configuration |
| `chore` | maintenance that fits nothing above |
| `revert` | reverting an earlier commit |

Rules the checker enforces:

- **Description**: imperative mood, lowercase first word, no trailing period. "add rate limiting",
  not "Added rate limiting." — it completes the sentence *"this commit will …"*.
- **Header length**: aim for ≤ 72 characters; 100 is a hard failure.
- **Blank line** between header and body.
- **Scope** is optional; use a real module or area name (`auth`, `wiki`, `codex-bridge`), not a
  vague one (`misc`, `stuff`).
- **Breaking changes**: `!` after the type/scope, *and* a `BREAKING CHANGE: <what and how to
  migrate>` footer. The `!` is the signal; the footer is the instruction.

Write a body when the change needs a *why*. Skip it when the header already says everything —
`chore: bump ruff to 0.6.2` needs no paragraph.

## Process

1. **Read what is staged**, not what is in the working tree:
   ```bash
   git status --short
   git diff --cached
   ```
   Nothing staged? Show `git status` and ask what to stage — never `git add -A` on the user's
   behalf, since it sweeps in files they may have left dirty deliberately.

2. **Check the recent style** so the message matches the project rather than this skill's
   defaults:
   ```bash
   git log --oneline -15
   ```
   If the repo does not use Conventional Commits at all, say so and ask before imposing it.

3. **Decide whether it is one commit.** If the staged diff does two unrelated things, say so and
   propose a split with the `git add -p` / `git reset` steps to get there. A commit that needs
   "and" in its description is usually two commits.

4. **Draft the message.** Derive it from the diff, not from the conversation — what the code now
   does, not what you were asked to do.

5. **Validate before committing**:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/commit/scripts/check_message.py" -m "<message>"
   ```

6. **Commit**:
   ```bash
   git commit -m "<header>" -m "<body>"
   ```
   Use `-F -` with a heredoc when the body has multiple paragraphs or footers.

7. **Report** the resulting `git log --oneline -1`. Do not push unless asked.

## Enforcement

Remembering is not a guarantee. Install the checker as a `commit-msg` hook and the rule holds for
every commit in the repo, from any tool or agent:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/commit/scripts/check_message.py" --install
```

It writes `.git/hooks/commit-msg` and refuses to clobber an existing hook. Removing the file
disables it. Hooks are local and not cloned, so each clone installs it once — mention that when
you set it up for someone.

Audit history that predates the hook:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/commit/scripts/check_message.py" --check-range origin/main..HEAD
```

Rewriting published history to strip trailers is a bigger decision than it looks — report what the
audit found and let the user choose, rather than reaching for `filter-branch` or `rebase -i`.

## Notes

- Merge, revert, `fixup!` and `squash!` headers are exempt from the format rule — git writes those
  — but never from the attribution rule.
- The checker reads a message file, so it doubles as a `commit-msg` hook and a pre-flight check.
- `TRIP-3-release` writes its own one-line release message and carries the same no-trailer rule;
  if a project uses both, keep the release message conventional too (`feat: …`, `fix: …`) so the
  history stays uniform.
