#!/usr/bin/env python3
"""Run a templated prompt through the OpenAI Codex plugin's companion runtime.

This replaces the bespoke `codex exec` wrapper scripts (start/resume/reset/show
plus a `jq` dependency) with a single call into the runtime that the
`codex` plugin already installs and keeps updated:

    node <plugin-cache>/plugins/codex/scripts/codex-companion.mjs task \
        --prompt-file <rendered> [--write] [--background] [--model M] [--effort E]

What this script owns, and the companion does not:

  * Prompt templates. `/codex:review` ships OpenAI's own review prompt and
    reviews only a git diff. TRIP needs prompts that read docs/archi/ and
    TRIP-review/checklist.md, suppress known false-positive classes, and end
    with APPROVED / REQUEST_CHANGES / NEEDS_REWORK. Those live in each skill's
    prompts/ directory and are rendered here.

  * Loop state. The companion tracks jobs per *workspace root* and can only
    `--resume-last`, so an alternating implement -> review -> implement loop
    would resume the wrong thread. Reviews are therefore run stateless: every
    turn is a fresh Codex run whose prompt carries the previous review via
    {{PRIOR_REVIEW}} and the implementer's replies via {{IMPLEMENTER_NOTES}}.
    Only `codex-implement` opts into --resume-last, where continuing the
    previous batch is the point and no other run intervenes.

Outputs are written to .codex-bridge/<target-key>.md in the repo (gitignored)
so the next turn can splice them in as {{PRIOR_REVIEW}}.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

STATE_DIRNAME = ".codex-bridge"
COMPANION_RELPATH = Path("plugins/codex/scripts/codex-companion.mjs")


def die(msg: str, code: int = 1) -> "None":
    print(f"error: {msg}", file=sys.stderr)
    raise SystemExit(code)


def find_companion() -> Path:
    """Locate codex-companion.mjs from the installed `codex` plugin.

    Order: $CODEX_COMPANION override, then the plugin cache. Cache directory
    names carry a version/commit suffix, so the newest match wins.
    """
    override = os.environ.get("CODEX_COMPANION")
    if override:
        p = Path(override).expanduser()
        if not p.is_file():
            die(f"$CODEX_COMPANION does not point at a file: {p}")
        return p

    config_dir = Path(os.environ.get("CLAUDE_CONFIG_DIR", Path.home() / ".claude"))
    cache = config_dir / "plugins" / "cache"
    if not cache.is_dir():
        die(
            "no plugin cache found. Install the Codex plugin first:\n"
            "  /plugin marketplace add openai/codex-plugin-cc\n"
            "  /plugin install codex@openai-codex"
        )

    matches = [p for p in cache.glob(f"*/{COMPANION_RELPATH}") if p.is_file()]
    matches += [p for p in cache.glob(f"*/*/{COMPANION_RELPATH}") if p.is_file()]
    if not matches:
        die(
            "the `codex` plugin is not installed (no codex-companion.mjs under "
            f"{cache}). Install it with:\n"
            "  /plugin marketplace add openai/codex-plugin-cc\n"
            "  /plugin install codex@openai-codex\n"
            "  /codex:setup\n"
            "Or point $CODEX_COMPANION at the script directly."
        )
    return max(matches, key=lambda p: p.stat().st_mtime)


def target_key(target: str) -> str:
    """Stable filesystem key for a target (a plan path or a free-form label)."""
    p = Path(target)
    if p.exists():
        target = str(p.resolve())
        try:
            target = str(Path(target).relative_to(Path.cwd()))
        except ValueError:
            pass
    key = target.lstrip("/").replace("/", "__")
    return re.sub(r"[^A-Za-z0-9._-]", "_", key)


def state_file(target: str) -> Path:
    return Path.cwd() / STATE_DIRNAME / f"{target_key(target)}.md"


def render(template: Path, values: dict[str, str]) -> str:
    """Substitute {{PLACEHOLDER}} tokens. Nothing else is expanded."""
    if not template.is_file():
        die(f"prompt template not found: {template}")
    text = template.read_text(encoding="utf-8")
    for name, value in values.items():
        text = text.replace("{{" + name + "}}", value)
    # Unfilled placeholders would reach Codex as literal noise.
    leftover = sorted(set(re.findall(r"\{\{([A-Z_]+)\}\}", text)))
    for name in leftover:
        text = text.replace("{{" + name + "}}", "")
    return text


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("target", help="plan path (docs/1-plans/F_*.plan.md) or free-form label")
    ap.add_argument("--prompt-file", required=True, help="prompt template to render")
    ap.add_argument("--extra", default="", help="trailing free-text context -> {{EXTRA_PROMPT}}")
    ap.add_argument("--notes", default="", help="implementer replies -> {{IMPLEMENTER_NOTES}}")
    ap.add_argument("--write", action="store_true", help="give Codex write access to the working tree")
    ap.add_argument("--resume-last", action="store_true", help="continue the workspace's last Codex thread")
    ap.add_argument("--background", action="store_true", help="detach; poll with /codex:status")
    ap.add_argument("--model", default=os.environ.get("CODEX_MODEL", ""))
    ap.add_argument("--effort", default=os.environ.get("CODEX_EFFORT", ""))
    ap.add_argument("--show", action="store_true", help="print the stored output and exit")
    ap.add_argument("--reset", action="store_true", help="drop stored output and exit")
    ap.add_argument("--dry-run", action="store_true", help="print the rendered prompt and exit")
    args = ap.parse_args()

    out_file = state_file(args.target)

    if args.show:
        if not out_file.is_file():
            die(f"no stored output for {args.target}")
        print(out_file.read_text(encoding="utf-8"))
        return 0

    if args.reset:
        if out_file.is_file():
            out_file.unlink()
            print(f"dropped {out_file}")
        else:
            print(f"nothing stored for {args.target}")
        return 0

    prior = out_file.read_text(encoding="utf-8") if out_file.is_file() else ""
    prompt = render(
        Path(args.prompt_file),
        {
            "TARGET": args.target,
            "EXTRA_PROMPT": args.extra,
            "IMPLEMENTER_NOTES": args.notes,
            "PRIOR_REVIEW": prior,
        },
    )

    if args.dry_run:
        print(prompt)
        return 0

    companion = find_companion()

    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as fh:
        fh.write(prompt)
        prompt_path = fh.name

    cmd = ["node", str(companion), "task", "--prompt-file", prompt_path]
    if args.write:
        cmd.append("--write")
    cmd.append("--resume-last" if args.resume_last else "--fresh")
    if args.background:
        cmd.append("--background")
    if args.model:
        cmd += ["--model", args.model]
    if args.effort:
        cmd += ["--effort", args.effort]

    print(f"codex-bridge: {Path(args.prompt_file).name} -> {args.target}", file=sys.stderr)
    print(f"  companion: {companion}", file=sys.stderr)
    print(f"  mode: {'write' if args.write else 'read-only'}"
          f"{', resume-last' if args.resume_last else ''}"
          f"{', background' if args.background else ''}", file=sys.stderr)
    if prior:
        print(f"  prior output spliced in from {out_file} ({len(prior)} chars)", file=sys.stderr)

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True)
    except FileNotFoundError:
        die("`node` not found on PATH; the Codex plugin runtime needs Node >= 18.18")
    finally:
        os.unlink(prompt_path)

    if proc.returncode != 0:
        sys.stderr.write(proc.stderr)
        die(f"codex-companion failed (rc={proc.returncode})", proc.returncode)

    output = proc.stdout
    if not args.background and output.strip():
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(output, encoding="utf-8")
        print(f"  stored: {out_file}", file=sys.stderr)

    sys.stdout.write(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
