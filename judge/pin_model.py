"""Pick the pinned Jev version once, from the models the account can use, and print it.

    JEV_MODEL=$(python -m judge.pin_model)

Prefers the newest listed name that carries a version number; aliases such as jev-latest are never chosen.
When the account's list carries only aliases (jev-latest, jev-preview), one minimal probe asks jev-latest and the
exact name that answers (response.model, for example jev-1.14.0) is pinned; the judge verifies that name the same
way on start, and the risk gate compares every decision against it.
Needs TYPESAFE_API_KEY in the environment, or JUDGE_AUTH=proxy where the environment proxy injects the key;
run it where the judge runs, never where the desk runs.
"""

from __future__ import annotations

import re
import sys
from collections.abc import Callable

from judge.jev import answering_model

RESOLVE_ALIAS = "jev-latest"

_VERSIONED = re.compile(r"^jev-(\d+)\.(\d+)(?:\.(\d+))?(?:-(\d+))?$")


def newest_pinned(names: list[str]) -> str | None:
    candidates = []
    for name in names:
        m = _VERSIONED.match(name)
        if m and "latest" not in name:
            candidates.append((tuple(int(g or 0) for g in m.groups()), name))
    return max(candidates)[1] if candidates else None


def choose_pinned(names: list[str], resolve: Callable[[str], str]) -> str | None:
    """The newest versioned name in the list, else the versioned name that answers for the alias, else None."""
    pinned = newest_pinned(names)
    if pinned is not None:
        return pinned
    if RESOLVE_ALIAS not in names:
        return None
    answered = resolve(RESOLVE_ALIAS)
    return newest_pinned([answered])


def main() -> int:
    try:
        from typesafe_sdk import TypeSafeClient
    except ImportError:
        print("typesafe-sdk is not installed", file=sys.stderr)
        return 2
    try:
        import os

        api_key = "injected-by-environment-proxy" if os.environ.get("JUDGE_AUTH") == "proxy" else None
        with TypeSafeClient(api_key=api_key, model=RESOLVE_ALIAS) as client:  # the alias lists models and answers one probe, never a decision
            names = [m.name for m in client.models.list().models]
            pinned = choose_pinned(names, lambda alias: answering_model(client, alias))
    except Exception as exc:  # noqa: BLE001 - report and fail, never guess a version
        print(f"could not pin a model: {type(exc).__name__}", file=sys.stderr)
        return 1
    if pinned is None:
        print(f"no versioned Jev model offered or answering for {RESOLVE_ALIAS}; available: {names}", file=sys.stderr)
        return 1
    print(pinned)
    return 0


if __name__ == "__main__":
    sys.exit(main())
