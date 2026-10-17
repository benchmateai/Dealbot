from __future__ import annotations

from dealbot.models import Alert
from dealbot.notifiers.base import Notifier, format_alert


class Slack(Notifier):
    name = "slack"
    requires = ("webhook_url",)

    def send(self, alerts: list[Alert]) -> None:
        blocks = []
        for a in alerts:
            d = a.deal
            price = f"${d.price:,.2f}" if d.price is not None else "n/a"
            if d.list_price is not None and a.discount_pct is not None:
                price += f" (was ${d.list_price:,.2f}, *{a.discount_pct}% off*)"
            text = (f"*<{d.url}|{d.title}>*\n{d.retailer} via {d.source} — {price}\n"
                    + ("_" + "; ".join(a.reasons) + "_" if a.reasons else ""))
            blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": f"`{a.score}/100` {text}"[:3000]}})
            blocks.append({"type": "divider"})
        for i in range(0, len(blocks), 48):
            payload = {"text": "\n\n".join(format_alert(a) for a in alerts)[:3000], "blocks": blocks[i:i + 48]}
            resp = self.http.post_json(self.options["webhook_url"], payload)
            if resp.status_code >= 300:
                self.log.error("slack webhook -> %s %s", resp.status_code, resp.text[:200])
