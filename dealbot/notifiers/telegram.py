from __future__ import annotations

import html

from dealbot.models import Alert
from dealbot.notifiers.base import Notifier


class Telegram(Notifier):
    name = "telegram"
    requires = ("bot_token", "chat_id")

    def send(self, alerts: list[Alert]) -> None:
        url = f"https://api.telegram.org/bot{self.options['bot_token']}/sendMessage"
        for a in alerts:
            d = a.deal
            price = f"${d.price:,.2f}" if d.price is not None else "n/a"
            if d.list_price is not None and a.discount_pct is not None:
                price += f" (was ${d.list_price:,.2f}, {a.discount_pct}% off)"
            msg = (f"<b>[{a.score}/100]</b> <a href=\"{html.escape(d.url, quote=True)}\">{html.escape(d.title)}</a>\n"
                   f"{html.escape(str(d.retailer))} via {d.source} — {price}\n"
                   f"<i>{html.escape('; '.join(a.reasons))}</i>")
            resp = self.http.post_json(url, {"chat_id": self.options["chat_id"], "text": msg[:4000],
                                             "parse_mode": "HTML", "disable_web_page_preview": False})
            if resp.status_code >= 300:
                self.log.error("telegram -> %s %s", resp.status_code, resp.text[:200])
