"""SQLite state: what we've already alerted on, and price history per item."""
from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from typing import Optional

from dealbot.models import Deal

SCHEMA = """
CREATE TABLE IF NOT EXISTS seen (
    key        TEXT PRIMARY KEY,
    source     TEXT NOT NULL,
    url        TEXT NOT NULL,
    title      TEXT NOT NULL,
    score      INTEGER NOT NULL,
    alerted    INTEGER NOT NULL DEFAULT 0,
    first_seen REAL NOT NULL,
    last_seen  REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS prices (
    key   TEXT NOT NULL,
    price REAL NOT NULL,
    ts    REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS prices_key ON prices(key, ts);
"""


class Store:
    def __init__(self, path: str | Path = "data/dealbot.db"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.path))
        self.conn.executescript(SCHEMA)

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "Store":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def was_alerted(self, deal: Deal) -> bool:
        row = self.conn.execute("SELECT alerted FROM seen WHERE key=?", (deal.key,)).fetchone()
        return bool(row and row[0])

    def prior_low(self, deal: Deal, exclude_current: bool = True) -> Optional[float]:
        row = self.conn.execute("SELECT MIN(price) FROM prices WHERE key=?", (deal.key,)).fetchone()
        return row[0] if row and row[0] is not None else None

    def record(self, deal: Deal, score: int, alerted: bool) -> None:
        now = time.time()
        self.conn.execute(
            """INSERT INTO seen(key, source, url, title, score, alerted, first_seen, last_seen)
               VALUES (?,?,?,?,?,?,?,?)
               ON CONFLICT(key) DO UPDATE SET
                 score=MAX(score, excluded.score),
                 alerted=MAX(alerted, excluded.alerted),
                 last_seen=excluded.last_seen""",
            (deal.key, deal.source, deal.url, deal.title, score, int(alerted), now, now),
        )
        if deal.price is not None:
            self.conn.execute("INSERT INTO prices(key, price, ts) VALUES (?,?,?)",
                              (deal.key, deal.price, now))
        self.conn.commit()

    def prune(self, max_age_days: int = 30) -> int:
        cutoff = time.time() - max_age_days * 86400
        cur = self.conn.execute("DELETE FROM seen WHERE last_seen < ?", (cutoff,))
        self.conn.execute("DELETE FROM prices WHERE ts < ?", (cutoff,))
        self.conn.commit()
        return cur.rowcount

    def recent_alerts(self, limit: int = 20) -> list[tuple]:
        return self.conn.execute(
            "SELECT title, url, score, first_seen FROM seen WHERE alerted=1 "
            "ORDER BY first_seen DESC LIMIT ?", (limit,)).fetchall()
