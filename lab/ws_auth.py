"""Signing Kalshi WebSocket handshakes for the lab with the production key in KALSHI_PROD_API_KEY_ID and
KALSHI_PROD_PRIVATE_KEY. RSA keys sign with RSA-PSS (SHA-256, salt = digest length) and Ed25519 keys sign
directly, over str(ms) + "GET" + "/trade-api/ws/v2" (docs/lab/kalshi_interfaces.md 1.2). The key is read
from the environment only and is never logged, written or passed to anything but the signer. The paper
desk never sees it: its chunk script removes it from the desk's environment."""

from __future__ import annotations

import base64
import os
import time
from collections.abc import Callable, Mapping

from kalshi.auth import load_private_key_bytes

KEY_ID_ENV = "KALSHI_PROD_API_KEY_ID"
KEY_ENV = "KALSHI_PROD_PRIVATE_KEY"
WS_PATH = "/trade-api/ws/v2"


def load_signer(env: Mapping[str, str] = os.environ) -> tuple[str, Callable[[bytes], bytes]] | None:
    """(key id, sign(bytes) -> signature) from the environment, or None when no production key is set."""
    key_id, raw = env.get(KEY_ID_ENV, "").strip(), env.get(KEY_ENV, "")
    if not key_id or not raw.strip():
        return None
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ed25519, padding, rsa

    data = load_private_key_bytes(raw)
    key = serialization.load_pem_private_key(data, password=None) if data.lstrip().startswith(b"-----BEGIN") else serialization.load_der_private_key(data, password=None)
    if isinstance(key, ed25519.Ed25519PrivateKey):
        return key_id, key.sign
    if isinstance(key, rsa.RSAPrivateKey):
        return key_id, lambda msg: key.sign(msg, padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.DIGEST_LENGTH), hashes.SHA256())
    raise ValueError("the production key is neither RSA nor Ed25519")


def ws_headers(key_id: str, sign: Callable[[bytes], bytes], *, path: str = WS_PATH, now_ms: int | None = None) -> dict[str, str]:
    ts = str(int(now_ms if now_ms is not None else time.time() * 1000))
    return {"KALSHI-ACCESS-KEY": key_id, "KALSHI-ACCESS-TIMESTAMP": ts, "KALSHI-ACCESS-SIGNATURE": base64.b64encode(sign((ts + "GET" + path).encode())).decode()}
