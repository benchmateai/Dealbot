from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from dealbot.http import Http
from dealbot.models import Alert


def format_alert(a: Alert) -> str:
    d = a.deal
    price = f"${d.price:,.2f}" if d.price is not None else "price n/a"
    if d.list_price is not None and a.discount_pct is not None:
        price += f" (list ${d.list_price:,.2f}, {a.discount_pct}% off)"
    lines = [
        f"[{a.score}/100] {d.title}",
        f"{d.retailer} via {d.source} — {price}",
        d.url,
    ]
    if a.reasons:
        lines.append("why: " + "; ".join(a.reasons))
    return "\n".join(lines)


class Notifier(ABC):
    name = "base"
    requires: tuple[str, ...] = ()

    def __init__(self, http: Http, options: dict[str, Any] | None = None):
        self.http = http
        self.options = options or {}
        self.log = logging.getLogger(f"dealbot.notify.{self.name}")

    def missing_requirements(self) -> list[str]:
        return [k for k in self.requires if not self.options.get(k)]

    @abstractmethod
    def send(self, alerts: list[Alert]) -> None:
        ...
