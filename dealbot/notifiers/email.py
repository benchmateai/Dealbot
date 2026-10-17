from __future__ import annotations

import smtplib
from email.message import EmailMessage

from dealbot.models import Alert
from dealbot.notifiers.base import Notifier, format_alert


class Email(Notifier):
    name = "email"
    requires = ("smtp_host", "from_addr", "to_addr")

    def send(self, alerts: list[Alert]) -> None:
        top = max(a.score for a in alerts)
        msg = EmailMessage()
        msg["Subject"] = f"Dealbot: {len(alerts)} possible pricing error(s), top score {top}"
        msg["From"] = self.options["from_addr"]
        msg["To"] = self.options["to_addr"]
        msg.set_content("\n\n".join(format_alert(a) for a in alerts))
        items = "".join(
            f'<li><b>[{a.score}]</b> <a href="{a.deal.url}">{a.deal.title}</a><br>'
            f'{a.deal.retailer} via {a.deal.source}'
            + (f' — ${a.deal.price:,.2f}' if a.deal.price is not None else '')
            + (f' (list ${a.deal.list_price:,.2f}, {a.discount_pct}% off)'
               if a.deal.list_price is not None and a.discount_pct is not None else '')
            + f'<br><i>{"; ".join(a.reasons)}</i></li>' for a in alerts)
        msg.add_alternative(f"<ul>{items}</ul>", subtype="html")

        host, port = self.options["smtp_host"], int(self.options.get("smtp_port", 587))
        with smtplib.SMTP(host, port, timeout=30) as s:
            if self.options.get("starttls", True):
                s.starttls()
            if self.options.get("username"):
                s.login(self.options["username"], self.options.get("password", ""))
            s.send_message(msg)
