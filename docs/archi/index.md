# Architecture index

## Distribution

- [[distribution]] — how the marketplace, per-plugin versioning, and `pocock-core` vendoring work.

## Plugins

- [[codex-bridge-plugin]] — stateless Codex CLI workers `trip` dispatches, and why they exist alongside `/codex:review`.
- [[pocock-core-plugin]] — the vendored subset of Matt Pocock's skills, and how it stays in sync.
- [[toolbox-plugin]] — standalone helpers: Conventional Commits enforcement, and an `AskUserQuestion` shim for non-Claude-Code agents.
- [[trip-plugin]] — the Plan/Implement/Release orchestration workflow and its agent-routing contract.
- [[trip-wiki-plugin]] — this wiki's own machinery: init, migrate, ingest, lint, query.
