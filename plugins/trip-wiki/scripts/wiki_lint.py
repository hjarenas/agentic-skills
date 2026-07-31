#!/usr/bin/env python3
"""Mechanical health checks for a docs/archi/ wiki.

Only the checks a script can settle without judgement live here: link
resolution, index coverage, frontmatter/body agreement, size, and whether cited
code paths still exist. The semantic checks — contradictions between pages,
claims the code has outgrown — are the model's job, and `wiki-lint` runs this
script first so the model spends its attention on those instead.

Exit codes: 0 clean, 1 findings, 2 no wiki found.

Usage:
    wiki_lint.py [--root docs/archi] [--json]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

WIKILINK = re.compile(r"\[\[([^\]|#]+)(?:[#|][^\]]*)?\]\]")
# path/to/file.ext optionally followed by :line — as used in "cite the code"
CODEREF = re.compile(r"`([\w./\-]+\.[A-Za-z0-9]{1,6})(?::\d+(?:-\d+)?)?`")
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.S)


def clean_scalar(value: str) -> str:
    """Strip quotes and any [[wikilink]] wrapper from a frontmatter value.

    Obsidian's property editor writes link-valued properties as `"[[slug]]"`,
    so `links: [auth-model]` and `links: ["[[auth-model]]"]` must both reduce
    to `auth-model` — otherwise editing a page in Obsidian invents drift
    findings that were never real.
    """
    value = value.strip().strip("'\"").strip()
    m = re.fullmatch(r"\[\[([^\]|#]+)(?:[#|][^\]]*)?\]\]", value)
    return m.group(1).strip() if m else value


def parse_frontmatter(text: str) -> dict:
    """Minimal YAML subset, no deps: `key: value`, `key: [a, b]`, and block
    sequences (`key:` followed by indented `- item` lines), which is the form
    Obsidian writes."""
    m = FRONTMATTER.match(text)
    if not m:
        return {}
    out: dict[str, object] = {}
    pending_key: str | None = None
    for line in m.group(1).splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        stripped = line.strip()

        # Continuation of a block sequence opened by a bare `key:`
        if stripped.startswith("- ") or stripped == "-":
            if pending_key is not None:
                if not isinstance(out.get(pending_key), list):
                    out[pending_key] = []   # the bare `key:` placeholder was a scalar
                item = clean_scalar(stripped[1:])
                if item:
                    out[pending_key].append(item)  # type: ignore[union-attr]
            continue

        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key, value = key.strip(), value.strip()
        pending_key = None

        if not value:
            # Either an empty scalar or the head of a block sequence; decided
            # by whether `- ` lines follow.
            pending_key = key
            out[key] = ""
        elif value.startswith("[") and value.endswith("]"):
            inner = value[1:-1]
            # `[[a]]` unquoted is one wikilink, not a list containing `[a]`.
            if value.startswith("[[") and value.endswith("]]"):
                out[key] = [clean_scalar(value)]
            else:
                out[key] = [clean_scalar(v) for v in inner.split(",") if v.strip()]
        else:
            out[key] = clean_scalar(value)
    return out


def body_of(text: str) -> str:
    m = FRONTMATTER.match(text)
    return text[m.end():] if m else text


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path, default=Path("docs/archi"))
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--size-limit", type=int, default=400, help="lines; SCHEMA.md overrides")
    args = ap.parse_args()

    root: Path = args.root
    pages_dir = root / "pages"
    index_file = root / "index.md"

    if not pages_dir.is_dir():
        print(f"no wiki at {root} (expected {pages_dir})", file=sys.stderr)
        return 2

    # SCHEMA.md may set its own size limit: "A page over 250 lines must be split."
    size_limit = args.size_limit
    schema = root / "SCHEMA.md"
    if schema.is_file():
        m = re.search(r"page\s+over\s+(\d+)\s+lines", schema.read_text(encoding="utf-8"), re.I)
        if m:
            size_limit = int(m.group(1))

    pages = {p.stem: p for p in sorted(pages_dir.glob("*.md"))}
    findings: list[dict] = []

    def add(kind: str, page: str, detail: str) -> None:
        findings.append({"check": kind, "page": page, "detail": detail})

    index_text = index_file.read_text(encoding="utf-8") if index_file.is_file() else ""
    if not index_file.is_file():
        add("missing-index", "index.md", "the wiki has no index.md")
    indexed = set(WIKILINK.findall(index_text))

    inbound: dict[str, int] = {slug: 0 for slug in pages}

    for slug, path in pages.items():
        text = path.read_text(encoding="utf-8")
        fm = parse_frontmatter(text)
        body = body_of(text)
        lines = text.count("\n") + 1

        if not fm:
            add("no-frontmatter", slug, "page has no frontmatter block")
        for required in ("title", "status", "updated"):
            if required not in fm:
                add("missing-field", slug, f"frontmatter is missing `{required}`")

        status = fm.get("status")
        if status and status not in ("current", "stale", "superseded"):
            add("bad-status", slug, f"status `{status}` is not current/stale/superseded")
        if status == "superseded" and not WIKILINK.search(body):
            add("dangling-superseded", slug, "marked superseded but names no replacement page")

        body_links = set(WIKILINK.findall(body))
        for target in sorted(body_links):
            if target == slug:
                add("self-link", slug, "page links to itself")
            elif target not in pages:
                add("broken-link", slug, f"[[{target}]] does not resolve to pages/{target}.md")
            else:
                inbound[target] += 1

        declared = set(fm.get("links") or [])
        for missing in sorted(declared - body_links):
            add("links-drift", slug, f"frontmatter declares `{missing}` but the body never links it")
        for missing in sorted(body_links - declared - {slug}):
            if missing in pages:
                add("links-drift", slug, f"body links [[{missing}]] but frontmatter omits it")

        for ref in sorted(set(CODEREF.findall(body))):
            if ref.startswith(("http", "docs/archi")) or "/" not in ref:
                continue
            if not Path(ref).exists():
                add("stale-coderef", slug, f"cites `{ref}`, which does not exist")

        if lines > size_limit:
            add("oversized", slug, f"{lines} lines exceeds the {size_limit}-line limit — split it")

        if slug not in indexed and index_file.is_file():
            add("unindexed", slug, "page is not listed in index.md")

    for target in sorted(indexed - set(pages)):
        add("broken-link", "index.md", f"[[{target}]] does not resolve to pages/{target}.md")

    for slug, count in sorted(inbound.items()):
        if count == 0 and slug in indexed:
            add("orphan", slug, "no other page links to it (indexed, but unreachable by link)")

    log_dir = root / "log"
    if log_dir.is_dir():
        for stray in sorted(log_dir.glob("*.md")):
            if not re.fullmatch(r"v\d+\.\d+\.\d+.*", stray.stem):
                add("log-naming", stray.name, "log files must be named v<x.y.z>.md — one per release")
    if (root / "log.md").is_file():
        add("log-monolith", "log.md", "a single append-only log conflicts on every merge; split it into log/v<x.y.z>.md")

    if args.json:
        print(json.dumps({"root": str(root), "pages": len(pages), "findings": findings}, indent=2))
    else:
        print(f"{len(pages)} pages under {pages_dir}")
        if not findings:
            print("no mechanical findings")
        else:
            by_check: dict[str, list[dict]] = {}
            for f in findings:
                by_check.setdefault(f["check"], []).append(f)
            for check in sorted(by_check):
                print(f"\n{check} ({len(by_check[check])})")
                for f in by_check[check]:
                    print(f"  {f['page']}: {f['detail']}")
            print(f"\n{len(findings)} findings")

    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
