"""Test isolation: the desk refuses to start when the Jev key is visible, so a developer or CI shell
that happens to carry the secrets must not leak them into the tests."""

import pytest

SECRET_VARS = ("TYPESAFE_API_KEY", "KALSHI_API_KEY_ID", "KALSHI_PRIVATE_KEY", "DESK_SECRET", "JUDGE_AUTH")


@pytest.fixture(autouse=True)
def _no_secrets_in_the_environment(monkeypatch):
    for name in SECRET_VARS:
        monkeypatch.delenv(name, raising=False)
