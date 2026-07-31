#!/usr/bin/env python3
"""Merge upstream changes into vendored skills, keeping local edits.

The vendored copies under `plugins/pocock-core/skills/` are ours to edit, but we
still want upstream's improvements. `UPSTREAM.json` pins the commit the current
copies were taken from, which gives us a **merge base**: for each file we can do
a real 3-way merge of

    base   = upstream file at the pinned commit
    ours   = the file as it exists in this repo now
    theirs = upstream file at the new commit

Files you never touched fast-forward cleanly. Files you edited merge, and only
genuinely overlapping edits produce conflict markers for you to resolve.

Usage:
    scripts/vendor-sync.py --check          # what changed upstream, no writes
    scripts/vendor-sync.py                  # merge upstream main into the vendored copies
    scripts/vendor-sync.py --ref v2.0.0     # merge a specific upstream ref
    scripts/vendor-sync.py --manifest path  # a different vendored plugin

After a successful merge the pinned commit and hashes in UPSTREAM.json are
rewritten, so the next run has an accurate base. Nothing is committed for you.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MANIFEST = REPO_ROOT / "plugins" / "pocock-core" / "UPSTREAM.json"
CACHE_DIR = REPO_ROOT / ".vendor-cache"


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, text=True, capture_output=True, **kw)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ensure_clone(repo_url: str) -> Path:
    """A bare-ish cache clone of upstream, reused across runs."""
    CACHE_DIR.mkdir(exist_ok=True)
    name = repo_url.rstrip("/").split("/")[-1].removesuffix(".git")
    clone = CACHE_DIR / name
    if not (clone / ".git").is_dir() and not (clone / "HEAD").is_file():
        print(f"cloning {repo_url} -> {clone}")
        r = run(["git", "clone", "--bare", repo_url, str(clone)])
        if r.returncode:
            sys.exit(f"clone failed:\n{r.stderr}")
    else:
        r = run(["git", "-C", str(clone), "fetch", "--all", "--tags", "--prune"])
        if r.returncode:
            sys.exit(f"fetch failed:\n{r.stderr}")
    return clone


def show(clone: Path, ref: str, path: str) -> bytes | None:
    r = subprocess.run(
        ["git", "-C", str(clone), "show", f"{ref}:{path}"],
        capture_output=True,
    )
    return r.stdout if r.returncode == 0 else None


def resolve(clone: Path, ref: str) -> str:
    """Resolve a ref in the cache clone. It is bare, so branches are local refs."""
    for candidate in (ref, f"refs/heads/{ref}", f"refs/tags/{ref}", f"origin/{ref}"):
        r = run(["git", "-C", str(clone), "rev-parse", "--verify", "--quiet", f"{candidate}^{{commit}}"])
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    sys.exit(f"cannot resolve ref {ref!r} in {clone}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    ap.add_argument("--ref", default=None, help="upstream ref to merge (default: the manifest's ref)")
    ap.add_argument("--check", action="store_true", help="report differences, write nothing")
    args = ap.parse_args()

    manifest = json.loads(args.manifest.read_text())
    upstream = manifest["upstream"]
    ref = args.ref or upstream.get("ref", "main")
    base_commit = upstream["commit"]

    clone = ensure_clone(upstream["repo"])
    new_commit = resolve(clone, ref)
    if new_commit == base_commit and not args.check:
        print(f"already at {base_commit[:12]} — nothing to merge")
        return 0

    print(f"base   {base_commit[:12]}")
    print(f"target {new_commit[:12]} ({ref})\n")

    unchanged, clean, conflicted, gone, locally_modified = [], [], [], [], []
    tmp = Path(tempfile.mkdtemp(prefix="vendor-sync-"))

    try:
        for entry in manifest["files"]:
            local = REPO_ROOT / entry["local"]
            up_path = entry["upstream"]

            base_blob = show(clone, base_commit, up_path)
            new_blob = show(clone, new_commit, up_path)

            if not local.is_file():
                print(f"  MISSING LOCALLY  {entry['local']}")
                continue

            if new_blob is None:
                gone.append(up_path)
                continue

            edited_locally = sha256(local) != entry["sha256"]
            if edited_locally:
                locally_modified.append(entry["local"])

            if base_blob == new_blob:
                unchanged.append(up_path)
                continue

            if args.check:
                mark = "!" if edited_locally else " "
                print(f"  {mark} upstream changed: {up_path}")
                continue

            if base_blob is None:
                # No merge base: upstream added it after our pin. Take theirs only
                # if we have nothing of our own there.
                if not edited_locally:
                    local.write_bytes(new_blob)
                    clean.append(up_path)
                else:
                    conflicted.append(up_path)
                continue

            base_f, ours_f, theirs_f = tmp / "base", tmp / "ours", tmp / "theirs"
            base_f.write_bytes(base_blob)
            theirs_f.write_bytes(new_blob)
            shutil.copyfile(local, ours_f)

            r = subprocess.run(
                ["git", "merge-file", "-L", "ours", "-L", f"base ({base_commit[:8]})",
                 "-L", f"upstream ({new_commit[:8]})", str(ours_f), str(base_f), str(theirs_f)],
                capture_output=True, text=True,
            )
            shutil.copyfile(ours_f, local)
            if r.returncode == 0:
                clean.append(up_path)
            elif r.returncode > 0:
                conflicted.append(up_path)
            else:
                sys.exit(f"git merge-file failed on {up_path}:\n{r.stderr}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if args.check:
        print(f"\n{len(unchanged)} unchanged upstream")
        if locally_modified:
            print(f"{len(locally_modified)} locally modified (marked ! above if also changed upstream):")
            for p in locally_modified:
                print(f"    {p}")
        if gone:
            print(f"{len(gone)} removed or renamed upstream:")
            for p in gone:
                print(f"    {p}")
        print("\nRun without --check to merge.")
        return 0

    print(f"\n  unchanged   {len(unchanged)}")
    print(f"  merged      {len(clean)}")
    print(f"  conflicted  {len(conflicted)}")
    for p in conflicted:
        print(f"      {p}")
    if gone:
        print(f"  vanished upstream {len(gone)} (left untouched):")
        for p in gone:
            print(f"      {p}")

    if conflicted:
        print("\nResolve the conflict markers, then re-run to refresh the pin.")
        print("The pin was NOT advanced, so the merge base is still valid.")
        return 1

    upstream["commit"] = new_commit
    upstream["ref"] = ref
    for entry in manifest["files"]:
        local = REPO_ROOT / entry["local"]
        if local.is_file():
            entry["sha256"] = sha256(local)
    args.manifest.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"\npin advanced to {new_commit[:12]}. Review `git diff` before committing.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
