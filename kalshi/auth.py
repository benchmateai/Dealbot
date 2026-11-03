"""Kalshi request signing: RSA-PSS over timestamp + method + path, sent as three headers.

Needs the `cryptography` package (pip install 'dealbot-desk[kalshi]'). The private key comes from the
environment as the PEM text or as its base64 on one line; it is never written anywhere. Public market
data needs no signing, so a feed without credentials still works for reading.
"""

from __future__ import annotations

import base64
import binascii
import os
import time
from collections.abc import Mapping

KEY_ID_ENV = "KALSHI_API_KEY_ID"
PRIVATE_KEY_ENV = "KALSHI_PRIVATE_KEY"
KEY_HEADER = "KALSHI-ACCESS-KEY"
SIGNATURE_HEADER = "KALSHI-ACCESS-SIGNATURE"
TIMESTAMP_HEADER = "KALSHI-ACCESS-TIMESTAMP"


class KalshiAuthError(RuntimeError):
    pass


def load_private_key_bytes(value: str) -> bytes:
    """Accept the PEM text itself, the base64 of the PEM file, or the base64 of the raw DER key (which is
    what the body of a PEM file is); return bytes that `KalshiAuth` can load."""
    text = (value or "").strip()
    if not text:
        raise KalshiAuthError("private key is empty")
    if text.startswith("-----BEGIN"):
        return text.encode() + b"\n"
    compact = "".join(text.split())
    try:
        decoded = base64.b64decode(compact + "=" * (-len(compact) % 4), validate=False)
    except (binascii.Error, ValueError) as exc:
        raise KalshiAuthError("private key is neither PEM text nor valid base64") from exc
    if decoded.lstrip().startswith(b"-----BEGIN") or decoded[:1] == b"\x30":
        return decoded
    raise KalshiAuthError("decoded private key is neither PEM nor DER")


load_private_key_pem = load_private_key_bytes


class KalshiAuth:
    def __init__(self, key_id: str, private_key_pem: bytes) -> None:
        try:
            from cryptography.hazmat.primitives import serialization
        except ImportError as exc:
            raise KalshiAuthError("the cryptography package is required for Kalshi signing: pip install 'dealbot-desk[kalshi]'") from exc
        if not key_id:
            raise KalshiAuthError("key id is empty")
        self.key_id = key_id
        try:
            if private_key_pem.lstrip().startswith(b"-----BEGIN"):
                self._key = serialization.load_pem_private_key(private_key_pem, password=None)
            else:
                self._key = serialization.load_der_private_key(private_key_pem, password=None)
        except (ValueError, TypeError) as exc:
            raise KalshiAuthError(f"private key could not be loaded: {type(exc).__name__}") from exc

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> KalshiAuth | None:
        env = os.environ if env is None else env
        key_id = (env.get(KEY_ID_ENV) or "").strip()
        pem = (env.get(PRIVATE_KEY_ENV) or "").strip()
        if not key_id and not pem:
            return None
        if not key_id or not pem:
            raise KalshiAuthError(f"both {KEY_ID_ENV} and {PRIVATE_KEY_ENV} are needed")
        return cls(key_id, load_private_key_bytes(pem))

    def sign(self, message: str) -> str:
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import padding

        signature = self._key.sign(message.encode(), padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.DIGEST_LENGTH), hashes.SHA256())
        return base64.b64encode(signature).decode()

    def headers(self, method: str, path: str, *, timestamp_ms: int | None = None) -> dict[str, str]:
        """Signed headers for `method` on `path` (the path without host or query string)."""
        ts = str(int(time.time() * 1000) if timestamp_ms is None else timestamp_ms)
        clean_path = path.split("?", 1)[0]
        return {KEY_HEADER: self.key_id, TIMESTAMP_HEADER: ts, SIGNATURE_HEADER: self.sign(ts + method.upper() + clean_path)}
