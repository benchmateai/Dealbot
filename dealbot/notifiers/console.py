from __future__ import annotations

from dealbot.models import Alert
from dealbot.notifiers.base import Notifier, format_alert


class Console(Notifier):
    name = "console"

    def send(self, alerts: list[Alert]) -> None:
        for a in alerts:
            print(format_alert(a))
            print("-" * 72)
