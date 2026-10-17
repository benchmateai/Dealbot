from __future__ import annotations

from dealbot.models import Alert
from dealbot.notifiers.base import Notifier


def _color(score: int) -> int:
    return 0xE53935 if score >= 85 else 0xFB8C00 if score >= 70 else 0xFDD835


class Discord(Notifier):
    name = "discord"
    requires = ("webhook_url",)

    def send(self, alerts: list[Alert]) -> None:
        # Discord accepts up to 10 embeds per message.
        for i in range(0, len(alerts), 10):
            embeds = []
            for a in alerts[i:i + 10]:
                d = a.deal
                fields = [{"name": "Retailer", "value": f"{d.retailer} (via {d.source})", "inline": True}]
                if d.price is not None:
                    val = f"${d.price:,.2f}"
                    if d.list_price is not None:
                        val += f" ~~${d.list_price:,.2f}~~"
                    if a.discount_pct is not None:
                        val += f" ({a.discount_pct}% off)"
                    fields.append({"name": "Price", "value": val, "inline": True})
                if a.reasons:
                    fields.append({"name": "Why", "value": "\n".join(f"• {r}" for r in a.reasons)[:1000]})
                embeds.append({
                    "title": d.title[:256], "url": d.url, "color": _color(a.score),
                    "description": f"Score **{a.score}/100**", "fields": fields,
                })
            payload = {"username": self.options.get("username", "Dealbot"), "embeds": embeds}
            resp = self.http.post_json(self.options["webhook_url"], payload)
            if resp.status_code >= 300:
                self.log.error("discord webhook -> %s %s", resp.status_code, resp.text[:200])
