"""Secret redaction for everything that is logged.

Two layers: exact values of configured secrets (the desk secret, and anything else handed in), and
patterns that look like credentials (bearer tokens, prefixed API keys, long hex strings). Keys whose
names look secret have their whole value replaced.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

REDACTED = "[REDACTED]"

_PATTERNS = (
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._\-]{8,}"),
    re.compile(r"\b(?:sk|ts|tsk|key|tok|api)[-_][A-Za-z0-9]{16,}\b"),
    re.compile(r"\b[a-fA-F0-9]{40,}\b"),
)
_SECRET_KEYS = ("secret", "token", "api_key", "apikey", "authorization", "password", "credential")


class Redactor:
    def __init__(self, secrets: Iterable[str] = ()) -> None:
        self._secrets = sorted({s for s in secrets if s and len(s) >= 8}, key=len, reverse=True)

    def redact_text(self, text: str) -> str:
        for secret in self._secrets:
            text = text.replace(secret, REDACTED)
        for pattern in _PATTERNS:
            text = pattern.sub(REDACTED, text)
        return text

    def redact(self, obj):
        if isinstance(obj, str):
            return self.redact_text(obj)
        if isinstance(obj, dict):
            out = {}
            for key, value in obj.items():
                key_text = self.redact_text(str(key))
                if any(marker in key_text.lower() for marker in _SECRET_KEYS):
                    out[key_text] = REDACTED
                else:
                    out[key_text] = self.redact(value)
            return out
        if isinstance(obj, (list, tuple)):
            return [self.redact(v) for v in obj]
        return obj
