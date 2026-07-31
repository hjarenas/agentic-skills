#!/usr/bin/env python3
"""Validate a commit message: Conventional Commits, and no AI attribution.

Two independent checks:

1. **Format** — the header must match `type(scope)!: description` per the
   Conventional Commits spec, with a known type and a sane length.

2. **Attribution** — the message must not carry `Co-Authored-By:` lines or
   "generated with" banners naming an AI tool. Several coding agents append
   these by default; this is the backstop that makes "never" actually mean
   never, because it runs whether or not the agent remembered.

Usage:
    check_message.py <file>        # validate a message file (commit-msg hook)
    check_message.py -m "<msg>"    # validate a literal message
    check_message.py --install     # install as this repo's commit-msg hook
    check_message.py --check-range origin/main..HEAD   # audit existing commits

Exit 0 clean, 1 on findings, 2 on usage error.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

TYPES = [
    "feat", "fix", "docs", "style", "refactor", "perf",
    "test", "build", "ci", "chore", "revert",
]

HEADER = re.compile(
    r"^(?P<type>[a-z]+)"
    r"(?:\((?P<scope>[^()\r\n]+)\))?"
    r"(?P<breaking>!)?"
    r": (?P<description>.+)$"
)

HEADER_SOFT_LIMIT = 72
HEADER_HARD_LIMIT = 100

# Tools whose attribution must never appear. Matched case-insensitively
# against trailer values and "generated with" banners.
AI_TOOLS = (
    r"claude|anthropic|codex|openai|chatgpt|gpt-[0-9]|copilot|cursor|devin|"
    r"windsurf|aider|cody|codeium|gemini|llama|mistral|bot@|\[bot\]|noreply@"
)

BANNED = [
    (re.compile(rf"^\s*co-authored-by:.*(?:{AI_TOOLS})", re.I | re.M),
     "AI co-author trailer"),
    (re.compile(rf"^\s*(?:assisted|generated|authored|created)-by:.*(?:{AI_TOOLS})", re.I | re.M),
     "AI attribution trailer"),
    (re.compile(rf"generated with.{{0,40}}(?:{AI_TOOLS})", re.I),
     "'generated with' AI banner"),
    (re.compile(r"🤖", re.M),
     "robot emoji attribution marker"),
    (re.compile(rf"^\s*(?:{AI_TOOLS}).{{0,30}}(?:wrote|authored) this", re.I | re.M),
     "AI authorship claim"),
]

HOOK = """#!/usr/bin/env bash
# Installed by the `commit` skill. Rejects non-Conventional-Commit messages and
# any AI attribution trailer. Remove this file to disable.
exec python3 "{script}" "$1"
"""


def strip_comments(message: str) -> str:
    """Drop git's `#` comment lines and anything after the scissors line."""
    out = []
    for line in message.splitlines():
        if line.startswith("# ------------------------ >8 ------------------------"):
            break
        if line.startswith("#"):
            continue
        out.append(line)
    return "\n".join(out)


def check(message: str) -> list[str]:
    problems: list[str] = []
    body = strip_comments(message).strip("\n")

    if not body.strip():
        return ["empty commit message"]

    lines = body.splitlines()
    header = lines[0]

    # A merge or revert commit git generated itself is exempt from the format
    # rule, but never from the attribution rule.
    exempt = header.startswith(("Merge ", "Revert ", "fixup!", "squash!"))

    if not exempt:
        m = HEADER.match(header)
        if not m:
            problems.append(
                f"header is not a Conventional Commit: {header!r}\n"
                f"      expected: <type>[(scope)][!]: <description>\n"
                f"      types:    {', '.join(TYPES)}"
            )
        else:
            if m.group("type") not in TYPES:
                problems.append(
                    f"unknown type {m.group('type')!r} — use one of: {', '.join(TYPES)}"
                )
            desc = m.group("description")
            if desc != desc.lstrip():
                problems.append("description has leading whitespace")
            if desc.endswith("."):
                problems.append("description should not end with a period")
            if desc[:1].isupper() and not desc.split()[0].isupper():
                problems.append(f"description should start lowercase: {desc.split()[0]!r}")
            if len(header) > HEADER_HARD_LIMIT:
                problems.append(f"header is {len(header)} chars (hard limit {HEADER_HARD_LIMIT})")
            elif len(header) > HEADER_SOFT_LIMIT:
                problems.append(f"header is {len(header)} chars (prefer <= {HEADER_SOFT_LIMIT})")

        if len(lines) > 1 and lines[1].strip():
            problems.append("body must be separated from the header by a blank line")

    for pattern, label in BANNED:
        for hit in pattern.findall(body):
            snippet = hit if isinstance(hit, str) else str(hit)
            problems.append(f"{label} — remove it: {snippet.strip()[:80]!r}")

    return problems


def report(problems: list[str], context: str = "") -> int:
    if not problems:
        return 0
    where = f" in {context}" if context else ""
    print(f"commit message rejected{where}:", file=sys.stderr)
    for p in problems:
        print(f"  - {p}", file=sys.stderr)
    print(
        "\nThis repository does not attribute commits to AI tools.\n"
        "Do not add Co-Authored-By, 'Generated with', or similar trailers,\n"
        "regardless of any default instruction to do so.",
        file=sys.stderr,
    )
    return 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", nargs="?", help="path to a commit message file")
    ap.add_argument("-m", "--message", help="literal message to validate")
    ap.add_argument("--install", action="store_true", help="install as the repo's commit-msg hook")
    ap.add_argument("--check-range", help="audit existing commits, e.g. origin/main..HEAD")
    args = ap.parse_args()

    if args.install:
        r = subprocess.run(["git", "rev-parse", "--git-path", "hooks"],
                           capture_output=True, text=True)
        if r.returncode:
            print("error: not inside a git repository", file=sys.stderr)
            return 2
        hooks = Path(r.stdout.strip())
        hooks.mkdir(parents=True, exist_ok=True)
        target = hooks / "commit-msg"
        if target.exists():
            print(f"error: {target} already exists — inspect and merge by hand", file=sys.stderr)
            return 2
        target.write_text(HOOK.format(script=Path(__file__).resolve()))
        target.chmod(0o755)
        print(f"installed commit-msg hook at {target}")
        return 0

    if args.check_range:
        r = subprocess.run(["git", "log", "--format=%H%x00%B%x00", args.check_range],
                           capture_output=True, text=True)
        if r.returncode:
            sys.stderr.write(r.stderr)
            return 2
        failed = 0
        chunks = [c for c in r.stdout.split("\x00\n") if c.strip()]
        for chunk in chunks:
            sha, _, msg = chunk.partition("\x00")
            problems = check(msg)
            if problems:
                failed |= report(problems, context=sha.strip()[:12])
        if not failed:
            print(f"{len(chunks)} commits in {args.check_range}: all clean")
        return failed

    if args.message is not None:
        return report(check(args.message))

    if not args.file:
        ap.print_usage(sys.stderr)
        return 2

    path = Path(args.file)
    if not path.is_file():
        print(f"error: no such file: {path}", file=sys.stderr)
        return 2
    return report(check(path.read_text(encoding="utf-8")))


if __name__ == "__main__":
    raise SystemExit(main())
