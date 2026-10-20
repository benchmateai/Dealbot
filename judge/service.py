"""The judge service: a small HTTP server that holds the Jev key, authenticates bots with the desk
secret, forwards each battery to Jev in one call and returns the raw answers. No trading logic.

    python -m judge.service --env-file .env.judge

Never logs request bodies, headers or keys: only decision ids, status codes, latency and model names.
"""

from __future__ import annotations

import argparse
import hmac
import json
import logging
import math
import os
import sys
import threading
from collections.abc import Mapping
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from judge.jev import JEV_KEY_ENV, STUB_MODEL, JevBackend, JudgeFault, StubBackend, TypeSafeBackend, ensure_pinned, sdk_version
from judge.protocol import HEALTH_PATH, JUDGE_PATH, MAX_BODY_BYTES, SECRET_HEADER, ProtocolError, parse_request

log = logging.getLogger("judge")
MIN_DESK_SECRET_CHARS = 32


class JudgeConfigError(ValueError):
    pass


@dataclass(frozen=True)
class JudgeConfig:
    bind: str
    port: int
    desk_secret: str = field(repr=False)
    model: str
    backend: str
    jev_timeout_s: float
    max_retries: int
    verify_model_on_start: bool

    @classmethod
    def from_env(cls, env: Mapping[str, str]) -> JudgeConfig:
        def get(key: str, default: str = "") -> str:
            value = env.get(key)
            return default if value is None or not value.strip() else value.strip()

        backend = get("JUDGE_BACKEND", "typesafe")
        if backend not in ("typesafe", "stub"):
            raise JudgeConfigError("JUDGE_BACKEND must be typesafe or stub")
        model = get("JEV_MODEL", STUB_MODEL if backend == "stub" else "")
        secret = get("DESK_SECRET")
        if len(secret) < MIN_DESK_SECRET_CHARS:
            raise JudgeConfigError(f"DESK_SECRET must be at least {MIN_DESK_SECRET_CHARS} characters; generate one with secrets.token_hex(32)")
        try:
            return cls(
                bind=get("JUDGE_BIND", "127.0.0.1"),
                port=int(get("JUDGE_PORT", "8787")),
                desk_secret=secret,
                model=ensure_pinned(model),
                backend=backend,
                jev_timeout_s=float(get("JEV_TIMEOUT_S", "8")),
                max_retries=int(get("JEV_MAX_RETRIES", "2")),
                verify_model_on_start=get("JUDGE_VERIFY_MODEL_ON_START", "1") not in ("0", "false", "no"),
            )
        except ValueError as exc:
            raise JudgeConfigError(str(exc)) from exc


def build_backend(cfg: JudgeConfig, env: Mapping[str, str]) -> JevBackend:
    if cfg.backend == "stub":
        return StubBackend(cfg.model)
    key = (env.get(JEV_KEY_ENV) or "").strip()
    if not key:
        raise JudgeConfigError(f"{JEV_KEY_ENV} is not set in the judge's environment (and must never be set in the desk's)")
    backend = TypeSafeBackend(key, cfg.model, max_retries=cfg.max_retries, retry_budget_s=max(cfg.jev_timeout_s * 2, 10.0), timeout_s=cfg.jev_timeout_s)
    if cfg.verify_model_on_start:
        backend.verify_model()
    return backend


def make_handler(backend: JevBackend, desk_secret: str, *, jev_timeout_s: float) -> type[BaseHTTPRequestHandler]:
    secret_bytes = desk_secret.encode()

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"
        server_version = "dealbot-judge/0.1"
        sys_version = ""

        def log_message(self, fmt: str, *args) -> None:  # noqa: D401 - silence the default access log (it prints paths and client IPs)
            return

        def _send(self, status: int, payload: dict, headers: dict[str, str] | None = None) -> None:
            body = json.dumps(payload).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            for name, value in (headers or {}).items():
                self.send_header(name, value)
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:
            if self.path == HEALTH_PATH:
                self._send(200, {"ok": True, "model": backend.model, "backend": backend.name, "sdk": sdk_version()})
            else:
                self._send(404, {"error": "not_found"})

        def do_POST(self) -> None:
            if self.path != JUDGE_PATH:
                self._send(404, {"error": "not_found"})
                return
            given = (self.headers.get(SECRET_HEADER) or "").encode()
            if not hmac.compare_digest(given, secret_bytes):
                self._send(401, {"error": "unauthorized"})
                return
            try:
                length = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                length = 0
            if length <= 0:
                self._send(400, {"error": "bad_request", "detail": "empty body", "retryable": False})
                return
            if length > MAX_BODY_BYTES:
                self._send(413, {"error": "bad_request", "detail": "body too large", "retryable": False})
                return
            try:
                request = parse_request(json.loads(self.rfile.read(length)))
            except (ProtocolError, ValueError) as exc:
                self._send(400, {"error": "bad_request", "detail": str(exc), "retryable": False})
                return
            timeout_s = jev_timeout_s
            if request.deadline_ms is not None:
                timeout_s = min(timeout_s, request.deadline_ms / 1000 - 0.05)
            if timeout_s < 0.1:
                self._send(504, {"error": "deadline_too_short", "detail": "not enough time left before the desk's next block", "retryable": True})
                return
            try:
                raw = backend.ask(request.state, request.questions, timeout_s=timeout_s)
            except JudgeFault as fault:
                headers = {}
                if fault.retry_after_ms:
                    headers["Retry-After"] = str(math.ceil(fault.retry_after_ms / 1000))
                log.warning("decision=%s bot=%s fault=%s status=%s retryable=%s", request.decision_id, request.bot, fault.code, fault.status, fault.retryable)
                self._send(fault.status, {"error": fault.code, "detail": str(fault), "retryable": fault.retryable, "retry_after_ms": fault.retry_after_ms}, headers)
                return
            except Exception as exc:  # noqa: BLE001 - never leak details of an unexpected failure to the caller
                log.error("decision=%s bot=%s unexpected %s", request.decision_id, request.bot, type(exc).__name__)
                self._send(500, {"error": "judge_error", "detail": type(exc).__name__, "retryable": True})
                return
            if raw.model != backend.model:
                log.warning("decision=%s model mismatch: requested=%s answered=%s", request.decision_id, backend.model, raw.model)
            log.info("decision=%s bot=%s model=%s latency_ms=%d request_id=%s", request.decision_id, request.bot, raw.model, raw.latency_ms, raw.request_id)
            self._send(
                200,
                {
                    "decision_id": request.decision_id,
                    "bot": request.bot,
                    "model": raw.model,
                    "requested_model": backend.model,
                    "answers": raw.answers,
                    "usage": raw.usage,
                    "request_id": raw.request_id,
                    "latency_ms": raw.latency_ms,
                    "backend": backend.name,
                },
            )

    return Handler


class _QuietServer(ThreadingHTTPServer):
    def handle_error(self, request, client_address) -> None:  # noqa: ARG002 - one line, no traceback, no client data
        log.warning("connection error: %s", type(sys.exc_info()[1]).__name__)


class JudgeServer:
    """Threaded server wrapper, also used by tests (port 0 picks a free port)."""

    def __init__(self, backend: JevBackend, desk_secret: str, *, bind: str = "127.0.0.1", port: int = 0, jev_timeout_s: float = 8.0) -> None:
        self._server = _QuietServer((bind, port), make_handler(backend, desk_secret, jev_timeout_s=jev_timeout_s))
        self._server.daemon_threads = True
        self._thread = threading.Thread(target=self._server.serve_forever, name="judge", daemon=True)

    @property
    def port(self) -> int:
        return self._server.server_address[1]

    @property
    def url(self) -> str:
        host, port = self._server.server_address[:2]
        return f"http://{host}:{port}"

    def start(self) -> JudgeServer:
        self._thread.start()
        return self

    def stop(self) -> None:
        self._server.shutdown()
        self._server.server_close()

    def serve_forever(self) -> None:
        self._server.serve_forever()


def load_env_file(path: str) -> dict[str, str]:
    values: dict[str, str] = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            value = value.split(" #", 1)[0].strip().strip("\"'")
            values[key.strip()] = value
    return values


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Dealbot judge service (holds the Jev key; returns raw answers)")
    parser.add_argument("--env-file", help="KEY=VALUE file; real environment variables take precedence")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    env: dict[str, str] = {}
    if args.env_file:
        env.update(load_env_file(args.env_file))
    env.update(os.environ)
    try:
        cfg = JudgeConfig.from_env(env)
        backend = build_backend(cfg, env)
    except (JudgeConfigError, ValueError, RuntimeError) as exc:
        print(f"judge: {exc}", file=sys.stderr)
        return 2
    server = JudgeServer(backend, cfg.desk_secret, bind=cfg.bind, port=cfg.port, jev_timeout_s=cfg.jev_timeout_s)
    log.info("serving on %s backend=%s model=%s sdk=%s", server.url, backend.name, backend.model, sdk_version())
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.stop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
