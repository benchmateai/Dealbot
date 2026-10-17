from dealbot.notifiers.base import Notifier, format_alert
from dealbot.notifiers.console import Console
from dealbot.notifiers.discord import Discord
from dealbot.notifiers.email import Email
from dealbot.notifiers.slack import Slack
from dealbot.notifiers.telegram import Telegram

REGISTRY: dict[str, type[Notifier]] = {cls.name: cls for cls in (Console, Discord, Slack, Telegram, Email)}

__all__ = ["REGISTRY", "Notifier", "format_alert"]
