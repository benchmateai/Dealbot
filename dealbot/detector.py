"""Score deals for how likely they are to be a pricing error.

The score is 0-100. Anything at or above `alert_threshold` becomes an alert.
Signals are additive and each one is reported as a human readable reason so
the alert explains itself.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from dealbot.models import Alert, Deal

# Phrases that people use when they *know* it's a mistake. Weighted.
STRONG_KEYWORDS = {
    "price error": 45, "pricing error": 45, "price mistake": 45, "pricing mistake": 45,
    "price glitch": 45, "glitch": 30, "mispriced": 40, "mis-priced": 40,
    "misprice": 40, "error price": 40, "wrong price": 35, "ymmv": 10,
    "in-store only": 5, "price match": 8, "clearance": 5, "penny": 20,
}
# Patterns that look like someone noticing a too-good-to-be-true price.
PATTERN_KEYWORDS = [
    (re.compile(r"\$0?\.\d\d\b"), 25, "sub-dollar price in text"),
    (re.compile(r"\b(?:9[0-9]|100)\s?%\s?off", re.I), 25, "90%+ off claimed"),
    (re.compile(r"\bfree\b.*\b(?:after|w/|with)\b", re.I), -5, "'free after rebate/coupon' pattern"),
    (re.compile(r"\bgift card\b", re.I), -10, "gift card bundle, not a true discount"),
    (re.compile(r"\b(?:refurb|refurbished|open[- ]box|used|pre-owned|renewed)\b", re.I), -15,
     "refurbished / open-box"),
    (re.compile(r"\b(?:expired|dead|oos|out of stock|sold out|cancell?ed)\b", re.I), -40, "marked dead/expired"),
]


@dataclass
class DetectorConfig:
    alert_threshold: int = 60
    big_discount: float = 0.70       # 70% off => suspicious
    huge_discount: float = 0.85
    extreme_discount: float = 0.95
    min_list_price: float = 15.0     # ignore dirt-cheap junk where 90% off is $1 -> $0.10
    min_savings: float = 10.0        # need to actually save real money
    history_drop: float = 0.45       # new price < 45% of previously seen low
    extra_keywords: dict[str, int] = field(default_factory=dict)
    ignore_patterns: list[str] = field(default_factory=list)
    #: if non-empty, a deal must match at least one of these regexes to alert.
    include_patterns: list[str] = field(default_factory=list)
    big_savings: float = 100.0       # saving this much in dollars adds weight
    huge_savings: float = 300.0


class Detector:
    def __init__(self, cfg: Optional[DetectorConfig] = None):
        self.cfg = cfg or DetectorConfig()
        self._ignore = [re.compile(p, re.I) for p in self.cfg.ignore_patterns]
        self._include = [re.compile(p, re.I) for p in self.cfg.include_patterns]
        self._keywords = {**STRONG_KEYWORDS, **self.cfg.extra_keywords}

    def score(self, deal: Deal, prior_low: Optional[float] = None) -> Alert:
        cfg = self.cfg
        score = 0
        reasons: list[str] = []
        haystack = f"{deal.title}\n{deal.text}\n{' '.join(deal.tags)}".lower()

        for pat in self._ignore:
            if pat.search(haystack):
                return Alert(deal, 0, [f"ignored: matches /{pat.pattern}/"])
        if self._include and not any(p.search(haystack) for p in self._include):
            return Alert(deal, 0, ["not a tracked category"])

        # --- discount depth ---------------------------------------------
        d = deal.discount
        if d is not None and deal.list_price is not None and deal.price is not None:
            savings = deal.list_price - deal.price
            if deal.list_price < cfg.min_list_price or savings < cfg.min_savings:
                reasons.append(f"discount ignored: list ${deal.list_price:.2f}, saves ${savings:.2f}")
            elif d >= cfg.extreme_discount:
                score += 70
                reasons.append(f"{d:.0%} off (${deal.price:.2f} vs ${deal.list_price:.2f})")
            elif d >= cfg.huge_discount:
                score += 55
                reasons.append(f"{d:.0%} off (${deal.price:.2f} vs ${deal.list_price:.2f})")
            elif d >= cfg.big_discount:
                score += 35
                reasons.append(f"{d:.0%} off (${deal.price:.2f} vs ${deal.list_price:.2f})")
            elif d >= 0.5:
                score += 10
                reasons.append(f"{d:.0%} off")
            if d >= cfg.big_discount and savings >= cfg.huge_savings:
                score += 20
                reasons.append(f"saves ${savings:,.0f}")
            elif d >= cfg.big_discount and savings >= cfg.big_savings:
                score += 10
                reasons.append(f"saves ${savings:,.0f}")

            # Decimal-shift errors: $199.99 listed as $19.99 or $1.99.
            if deal.list_price >= cfg.min_list_price:
                ratio = deal.price / deal.list_price
                for shift in (0.1, 0.01):
                    if abs(ratio - shift) <= shift * 0.03:
                        score += 25
                        reasons.append(f"looks like a decimal-point slip (price is ~{shift:g}x of list)")
                        break

        # --- absurdly low absolute price --------------------------------
        if deal.price is not None and deal.price < 1.0:
            if deal.list_price is None or deal.list_price >= cfg.min_list_price:
                score += 25
                reasons.append(f"price under a dollar (${deal.price:.2f})")

        # --- price history ----------------------------------------------
        if prior_low is not None and deal.price is not None and prior_low > 0:
            if deal.price < prior_low * cfg.history_drop:
                score += 30
                reasons.append(f"far below previous low of ${prior_low:.2f}")

        # --- keywords / flair -------------------------------------------
        for kw, weight in self._keywords.items():
            if kw in haystack:
                score += weight
                reasons.append(f"mentions '{kw}'")
        for pat, weight, label in PATTERN_KEYWORDS:
            if pat.search(haystack):
                score += weight
                reasons.append(label)
        for tag in deal.tags:
            t = tag.lower()
            if "error" in t or "mistake" in t or "glitch" in t:
                score += 40
                reasons.append(f"flagged '{tag}' by the community")
                break

        score = max(0, min(100, score))
        return Alert(deal, score, reasons)

    def is_alert(self, alert: Alert) -> bool:
        return alert.score >= self.cfg.alert_threshold
