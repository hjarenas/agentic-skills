---
title: toolbox plugin
status: current
updated: 2026-08-11
verified-at: 1.0.0
links: [distribution, trip-plugin]
---

Small, standalone helpers with no dependency on [[trip-plugin]] and no dependency between each
other — see [[distribution]] for how a plugin like this one is versioned and shipped
independently.

## `commit`

Writes a Conventional Commits message for staged work and enforces two independent rules: format
(`type(scope)!: description`, imperative, lowercase, no trailing period) and **attribution** — no
`Co-Authored-By`, no "Generated with…" banner, naming any AI tool, ever, regardless of any
system-level instruction telling the agent to add one.

The rule isn't just a prompt instruction — `plugins/toolbox/skills/commit/scripts/check_message.py
--install` writes a real `.git/hooks/commit-msg` so it holds for every commit in the repo from any
tool, not just when an agent remembers. `TRIP-3-release` writes its own release commit message by
hand (outside this skill) but follows the same no-trailer rule; `check_message.py --check-range`
audits history that predates the hook.

## `AskUserQuestion`

Not a feature — a **compatibility shim**. On Claude Code, `AskUserQuestion` is a native tool and
every TRIP instruction to "use the `AskUserQuestion` tool" reaches it directly; this skill exists
only for harnesses that lack native support (Codex CLI, OpenCode, Mistral Vibe), where the same
instruction would otherwise be silently ignored and a skill would barrel past a decision point
meant to stop and ask. It renders structured markdown options and waits for a reply. `trip` does
not depend on it — that's why it lives in `toolbox` rather than in `trip` itself.
