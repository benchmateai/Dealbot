#!/usr/bin/env python3
"""The review gate: a commit that touches money code (ops/money_paths.txt) is pushed only when its message
carries a `Reviewed-by:` trailer, which the coordinator adds once a fresh reviewer has read the change and every
finding is fixed or answered (ops/TEAM.md, "Review before push").

As git's pre-push hook (ops/hooks/pre-push, active in the coordinator's clone through
`git config core.hooksPath ops/hooks`) it reads the refs being pushed on stdin and refuses the push when a
commit in them lacks the trailer. By hand:

    python3 ops/review_gate.py --range origin/claude/desk-skeleton..HEAD
"""

from __future__ import annotations

import argparse
import fnmatch
import subprocess
import sys
from pathlib import Path

ZERO = "0" * 40
PATHS = Path(__file__).resolve().parent / "money_paths.txt"
TRAILER = "Reviewed-by:"


def patterns(path: str | Path = PATHS) -> list[str]:
    return [ln.strip() for ln in Path(path).read_text().splitlines() if ln.strip() and not ln.strip().startswith("#")]


def is_money(file: str, pats: list[str]) -> bool:
    return any(file.startswith(p) if p.endswith("/") else fnmatch.fnmatch(file, p) for p in pats)


def _git(*args: str, cwd: str | None = None) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True, cwd=cwd).stdout


def commits(local_sha: str, remote_sha: str, cwd: str | None = None) -> list[str]:
    """The commits a push of local_sha over remote_sha adds, merges left out."""
    if local_sha == ZERO:  # deleting a branch adds nothing
        return []
    if remote_sha != ZERO:
        try:
            return _git("rev-list", "--no-merges", f"{remote_sha}..{local_sha}", cwd=cwd).split()
        except subprocess.CalledProcessError:
            pass  # the remote's commit is not known here: fall back to what no remote branch has
    return _git("rev-list", "--no-merges", local_sha, "--not", "--remotes", cwd=cwd).split()


def unreviewed(shas: list[str], pats: list[str], cwd: str | None = None) -> list[tuple[str, str, list[str]]]:
    """(sha, subject, money files) for each commit that touches money code without the trailer."""
    out = []
    for sha in shas:
        files = _git("diff-tree", "--no-commit-id", "--name-only", "-r", "--root", sha, cwd=cwd).split()
        money = [f for f in files if is_money(f, pats)]
        if not money:
            continue
        body = _git("log", "-1", "--format=%B", sha, cwd=cwd)
        if not any(ln.strip().startswith(TRAILER) for ln in body.splitlines()):
            out.append((sha, body.splitlines()[0] if body else "", money))
    return out


def report(bad: list[tuple[str, str, list[str]]]) -> str:
    lines = ["review gate: these commits touch money code but carry no Reviewed-by: trailer (ops/TEAM.md, \"Review before push\"):"]
    for sha, subject, files in bad:
        shown = ", ".join(files[:5]) + (f" and {len(files) - 5} more" if len(files) > 5 else "")
        lines.append(f"  {sha[:8]} {subject}  ({shown})")
    lines.append("Have a fresh reviewer read the change (ops/review_prompt.md), fix or answer every finding, then add the trailer.")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Refuse money-code commits that no fresh reviewer has read")
    parser.add_argument("--hook", action="store_true", help="run as git's pre-push hook (refs on stdin)")
    parser.add_argument("--range", default=None, help="check the commits in A..B instead")
    parser.add_argument("remote", nargs="*", help="(the hook's arguments: remote name and URL)")
    args = parser.parse_args(argv)
    pats = patterns()
    shas: list[str] = []
    if args.range:
        shas = _git("rev-list", "--no-merges", args.range).split()
    else:
        for ln in sys.stdin.read().splitlines():
            parts = ln.split()
            if len(parts) == 4:
                shas += [s for s in commits(parts[1], parts[3]) if s not in shas]
    bad = unreviewed(shas, pats)
    if bad:
        print(report(bad), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
