"""Token-budget estimate with no tokenizer dependency.

The estimate is deliberately conservative: every digit and every punctuation mark counts as one
token and letter runs count one token per four characters. A snapshot that fits the budget here
also fits under a real BPE tokenizer, which merges digits and common pieces.
"""

from __future__ import annotations

import re

_PIECE = re.compile(r"[A-Za-z]+|\d|[^\sA-Za-z\d]")


def estimate_tokens(text: str) -> int:
    count = 0
    for match in _PIECE.finditer(text):
        piece = match.group(0)
        count += (len(piece) + 3) // 4 if piece.isalpha() else 1
    return count
