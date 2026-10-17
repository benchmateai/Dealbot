"""Pull prices out of free text like deal titles.

Deal titles look like:
    "Sony WH-1000XM5 Headphones $29.99 (reg. $399.99) + free shipping"
    "Dyson V15 - $65 (was $749)"
    "90% off: LEGO Star Wars UCS set, $59.99"
"""
from __future__ import annotations

import re
from typing import Optional

_MONEY = r"\$\s?(\d{1,3}(?:,\d{3})+|\d+)(?:\.(\d{1,2}))?"
MONEY_RE = re.compile(_MONEY)

# Words that introduce the *original* price.
_LIST_WORDS = r"(?:reg(?:ular(?:ly)?)?\.?|was|orig(?:inally)?\.?|list|msrp|retail|compare(?: at)?|normally|value|off of)"
LIST_RE = re.compile(_LIST_WORDS + r"\s*(?:price)?\s*:?\s*(?:of\s*)?" + _MONEY, re.I)
# "$X off" style is a saving, not a list price; "(... $Y)" after price is usually list.
PCT_OFF_RE = re.compile(r"(\d{1,3})\s?%\s?off", re.I)
PAREN_PRICE_RE = re.compile(r"\(\s*" + _MONEY + r"\s*\)")
# "$399 now $29", "$399 -> $29", "$399 drops to $29": first figure is the list price.
LIST_FIRST_RE = re.compile(_MONEY + r"\s*(?:now|->|→|down to|drops? to|to|reduced to)\s*" + _MONEY, re.I)


def _to_float(whole: str, cents: Optional[str]) -> float:
    return float(whole.replace(",", "")) + (float("0." + cents) if cents else 0.0)


def all_prices(text: str) -> list[float]:
    return [_to_float(w, c) for w, c in MONEY_RE.findall(text)]


def parse_prices(text: str) -> tuple[Optional[float], Optional[float]]:
    """Return (price, list_price) guessed from text. Either may be None."""
    if not text:
        return None, None
    list_price: Optional[float] = None
    m = LIST_RE.search(text)
    if m:
        list_price = _to_float(m.group(1), m.group(2))
    else:
        m = LIST_FIRST_RE.search(text)
        if m:
            first, second = _to_float(m.group(1), m.group(2)), _to_float(m.group(3), m.group(4))
            if first > second:
                return second, first
    prices = all_prices(text)
    if not prices:
        return None, list_price

    candidates = [p for p in prices if list_price is None or p != list_price]
    price: Optional[float]
    if candidates:
        # "A for $X" and "$X" alone: the sale price is almost always the first
        # dollar figure that is not the list price. "$X off" figures are savings.
        price = None
        for mm in MONEY_RE.finditer(text):
            val = _to_float(mm.group(1), mm.group(2))
            tail = text[mm.end():mm.end() + 8].lower().lstrip()
            if tail.startswith("off"):
                continue
            if list_price is not None and val == list_price:
                continue
            price = val
            break
        if price is None:
            price = min(candidates)
    else:
        price = None

    # If no explicit list price but there is a "NN% off", back it out.
    if list_price is None and price is not None:
        pm = PCT_OFF_RE.search(text)
        if pm:
            pct = int(pm.group(1))
            if 0 < pct < 100:
                list_price = round(price / (1 - pct / 100), 2)
        else:
            # "$29.99 ($399.99)" convention: parenthesized bigger number is list.
            for pw, pc in PAREN_PRICE_RE.findall(text):
                v = _to_float(pw, pc)
                if v > price:
                    list_price = v
                    break
    if list_price is not None and price is not None and list_price < price:
        # Mis-ordered ("$399 now $29"): assume the larger is list.
        price, list_price = min(price, list_price), max(price, list_price)
    return price, list_price
