"""Question batteries: one file per bot type, one judgment per question, every Choice has "other"."""

from __future__ import annotations

import importlib

from questions.schema import OTHER, OTHER_TEXT, Battery, BatteryError, ChoiceQ, NoulQ, Resolution, ScoreQ

BOTS = ("gambler", "house", "spy")

__all__ = ["BOTS", "OTHER", "OTHER_TEXT", "Battery", "BatteryError", "ChoiceQ", "NoulQ", "Resolution", "ScoreQ", "load_battery"]


def load_battery(bot: str) -> Battery:
    if bot not in BOTS:
        raise BatteryError(f"unknown bot {bot!r}; expected one of {BOTS}")
    return importlib.import_module(f"questions.{bot}").BATTERY
