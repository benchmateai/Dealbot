"""Serve the desk dashboard: the page at /, the aggregated state at /api/state, and one decision's
full detail at /api/decision/<id>. A background thread tails the log every few seconds.

    python -m dashboard.serve --log-dir logs/data [--port 8080] [--bind 127.0.0.1]
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import threading
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from dashboard.state import DeskState
from dashboard.tail import EventTailer
from reports.trials import evaluate as evaluate_trials
from trials.registry import TrialRegistry

log = logging.getLogger("dashboard")
STATIC_DIR = Path(__file__).resolve().parent / "static"
INDEX_FILE = STATIC_DIR / "index.html"
DOCTYPE_PREFIX = b'<!doctype html>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
TRIALS_CACHE_SECONDS = 60.0


class Dashboard:
    def __init__(self, log_dir: str | Path, trials_file: str | Path | None = None, *, state: DeskState | None = None) -> None:
        self._log_dir = Path(log_dir)
        self._trials_file = Path(trials_file) if trials_file else self._log_dir / "trials.json"
        self._tailer = EventTailer(self._log_dir)
        self._state = state or DeskState()
        self._lock = threading.Lock()
        self._trials_cache: tuple[float, dict] | None = None

    @property
    def state(self) -> DeskState:
        return self._state

    def refresh(self) -> int:
        records = self._tailer.poll()
        with self._lock:
            for rec in records:
                self._state.ingest(rec)
        return len(records)

    def trials(self) -> dict:
        now = time.monotonic()
        if self._trials_cache is not None and now - self._trials_cache[0] < TRIALS_CACHE_SECONDS:
            return self._trials_cache[1]
        view: dict = {"n_registered": 0, "n_used": 0, "n_evaluated": 0, "var_source": None, "min_backtest_years": {}, "rows": []}
        if self._trials_file.exists():
            registry = TrialRegistry(self._trials_file)
            report = evaluate_trials(registry, self._log_dir, persist=False)
            view = {
                "n_registered": report.n_registered,
                "n_used": report.n_trials,
                "n_evaluated": report.n_evaluated,
                "var_source": report.var_source,
                "min_backtest_years": {str(k): round(v, 2) for k, v in report.min_backtest_years.items()},
                "rows": [row.__dict__ for row in report.rows],
            }
        self._trials_cache = (now, view)
        return view

    def payload(self, *, include_details: bool = False, source_mode: str = "live") -> dict:
        with self._lock:
            payload = self._state.to_payload(include_details=include_details)
        payload["trials"] = self.trials()
        payload["source"] = {"mode": source_mode, "log_dir": str(self._log_dir), "trials_file": str(self._trials_file)}
        return payload

    def decision(self, decision_id: str) -> dict | None:
        with self._lock:
            return self._state.decision_detail(decision_id)


def index_document() -> bytes:
    return DOCTYPE_PREFIX + INDEX_FILE.read_bytes()


def make_handler(dashboard: Dashboard) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"
        server_version = "dealbot-dashboard/0.1"
        sys_version = ""

        def log_message(self, fmt: str, *args) -> None:
            return

        def _send(self, status: int, body: bytes, content_type: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _json(self, status: int, payload) -> None:
            self._send(status, json.dumps(payload, separators=(",", ":")).encode(), "application/json")

        def do_GET(self) -> None:
            path = urllib.parse.urlsplit(self.path).path
            if path in ("/", "/index.html"):
                self._send(200, index_document(), "text/html; charset=utf-8")
            elif path == "/api/state":
                self._json(200, dashboard.payload())
            elif path.startswith("/api/decision/"):
                decision_id = urllib.parse.unquote(path[len("/api/decision/"):])
                detail = dashboard.decision(decision_id)
                self._json(200, detail) if detail is not None else self._json(404, {"error": "unknown decision"})
            elif path == "/healthz":
                self._json(200, {"ok": True})
            elif path == "/favicon.ico":
                self.send_response(204)
                self.send_header("Content-Length", "0")
                self.end_headers()
            else:
                self._json(404, {"error": "not found"})

    return Handler


class _QuietServer(ThreadingHTTPServer):
    def handle_error(self, request, client_address) -> None:  # noqa: ARG002
        log.warning("connection error: %s", type(sys.exc_info()[1]).__name__)


class DashboardServer:
    def __init__(self, dashboard: Dashboard, *, bind: str = "127.0.0.1", port: int = 0, poll_seconds: float = 2.0) -> None:
        self._dashboard = dashboard
        self._server = _QuietServer((bind, port), make_handler(dashboard))
        self._server.daemon_threads = True
        self._poll_seconds = poll_seconds
        self._stop = threading.Event()
        self._serve_thread = threading.Thread(target=self._server.serve_forever, name="dashboard-http", daemon=True)
        self._poll_thread = threading.Thread(target=self._poll_loop, name="dashboard-tail", daemon=True)

    @property
    def url(self) -> str:
        host, port = self._server.server_address[:2]
        return f"http://{host}:{port}"

    def _poll_loop(self) -> None:
        while not self._stop.is_set():
            try:
                self._dashboard.refresh()
            except Exception as exc:  # noqa: BLE001 - keep tailing on a bad line or a transient file error
                log.warning("refresh failed: %s", type(exc).__name__)
            self._stop.wait(self._poll_seconds)

    def start(self) -> DashboardServer:
        self._dashboard.refresh()
        self._serve_thread.start()
        self._poll_thread.start()
        return self

    def stop(self) -> None:
        self._stop.set()
        self._server.shutdown()
        self._server.server_close()

    def wait(self) -> None:
        try:
            while not self._stop.is_set():
                self._stop.wait(1.0)
        except KeyboardInterrupt:
            pass


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Dealbot desk dashboard (read-only)")
    parser.add_argument("--log-dir", default="logs/data")
    parser.add_argument("--trials-file", default=None, help="default: <log-dir>/trials.json")
    parser.add_argument("--bind", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--poll-seconds", type=float, default=2.0)
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    server = DashboardServer(Dashboard(args.log_dir, args.trials_file), bind=args.bind, port=args.port, poll_seconds=args.poll_seconds).start()
    log.info("dashboard on %s tailing %s", server.url, args.log_dir)
    try:
        server.wait()
    finally:
        server.stop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
