"""One shared HTTP session: identifiable user agent, timeouts, retries, politeness."""
from __future__ import annotations

import logging
import threading
import time
from urllib.parse import urlsplit

import requests
from requests.adapters import HTTPAdapter

log = logging.getLogger(__name__)

USER_AGENT = "dealbot/0.1 (+https://github.com/benchmateai/dealbot; price-error monitor)"
DEFAULT_TIMEOUT = 20


class Http:
    def __init__(self, user_agent: str = USER_AGENT, min_interval: float = 1.0, retries: int = 2):
        self.session = requests.Session()
        self.session.headers["User-Agent"] = user_agent
        self.session.headers["Accept"] = "application/json, application/rss+xml, text/html;q=0.9, */*;q=0.8"
        self.session.mount("https://", HTTPAdapter(pool_maxsize=8))
        self.min_interval = min_interval
        self.retries = retries
        self._last: dict[str, float] = {}
        self._lock = threading.Lock()

    def _throttle(self, url: str) -> None:
        host = urlsplit(url).netloc
        with self._lock:
            wait = self._last.get(host, 0) + self.min_interval - time.monotonic()
            if wait > 0:
                time.sleep(wait)
            self._last[host] = time.monotonic()

    def get(self, url: str, **kw) -> requests.Response:
        kw.setdefault("timeout", DEFAULT_TIMEOUT)
        delay = 2.0
        for attempt in range(self.retries + 1):
            self._throttle(url)
            try:
                resp = self.session.get(url, **kw)
            except requests.RequestException as e:
                if attempt == self.retries:
                    raise
                log.warning("GET %s failed (%s), retrying in %.0fs", url, e, delay)
            else:
                if resp.status_code in (429, 500, 502, 503, 504) and attempt < self.retries:
                    retry_after = resp.headers.get("Retry-After")
                    sleep_for = float(retry_after) if retry_after and retry_after.isdigit() else delay
                    log.warning("GET %s -> %s, retrying in %.0fs", url, resp.status_code, sleep_for)
                    time.sleep(sleep_for)
                    delay *= 2
                    continue
                return resp
            time.sleep(delay)
            delay *= 2
        raise RuntimeError("unreachable")

    def post_json(self, url: str, payload: dict, **kw) -> requests.Response:
        kw.setdefault("timeout", DEFAULT_TIMEOUT)
        return self.session.post(url, json=payload, **kw)
