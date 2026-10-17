from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Iterable

from dealbot.http import Http
from dealbot.models import Deal


class Source(ABC):
    """A place deals come from. Subclasses yield Deal objects from fetch()."""

    name: str = "base"
    #: env/config keys that must be non-empty for this source to run.
    requires: tuple[str, ...] = ()

    def __init__(self, http: Http, options: dict[str, Any] | None = None):
        self.http = http
        self.options = options or {}
        self.log = logging.getLogger(f"dealbot.sources.{self.name}")

    def missing_requirements(self) -> list[str]:
        return [k for k in self.requires if not self.options.get(k)]

    @abstractmethod
    def fetch(self) -> Iterable[Deal]:
        ...
