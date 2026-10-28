"""Pick the pinned Jev version once, from the models the account can use, and print it.

    JEV_MODEL=$(python -m judge.pin_model)

Prefers the newest name that carries a version number; aliases such as jev-latest are never chosen.
Needs TYPESAFE_API_KEY in the environment, so run it where the judge runs, never where the desk runs.
"""

from __future__ import annotations

import re
import sys

_VERSIONED = re.compile(r"^jev-(\d+)\.(\d+)(?:\.(\d+))?(?:-(\d+))?$")


def newest_pinned(names: list[str]) -> str | None:
    candidates = []
    for name in names:
        m = _VERSIONED.match(name)
        if m and "latest" not in name:
            candidates.append((tuple(int(g or 0) for g in m.groups()), name))
    return max(candidates)[1] if candidates else None


def main() -> int:
    try:
        from typesafe_sdk import TypeSafeClient
    except ImportError:
        print("typesafe-sdk is not installed", file=sys.stderr)
        return 2
    try:
        with TypeSafeClient(model="jev-latest") as client:  # the alias is only used to list models, never to answer
            names = [m.name for m in client.models.list().models]
    except Exception as exc:  # noqa: BLE001 - report and fail, never guess a version
        print(f"could not list models: {type(exc).__name__}", file=sys.stderr)
        return 1
    pinned = newest_pinned(names)
    if pinned is None:
        print(f"no versioned Jev model offered; available: {names}", file=sys.stderr)
        return 1
    print(pinned)
    return 0


if __name__ == "__main__":
    sys.exit(main())
