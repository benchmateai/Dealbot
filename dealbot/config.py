"""Load config.yaml, expanding ${ENV_VAR} references and a local .env file."""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml

from dealbot.detector import DetectorConfig

_ENV_RE = re.compile(r"\$\{([A-Z0-9_]+)(?::-([^}]*))?\}")

DEFAULTS: dict[str, Any] = {
    "db_path": "data/dealbot.db",
    "interval_minutes": 10,
    "max_alerts_per_run": 25,
    "prune_days": 30,
    "http": {"min_interval_seconds": 1.0},
    "detector": {},
    "sources": {},
    "notifiers": {"console": {"enabled": True}},
}


def load_dotenv(path: str | Path = ".env") -> None:
    p = Path(path)
    if not p.exists():
        return
    for line in p.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        v = v.split(" #", 1)[0].strip().strip('"').strip("'")
        os.environ.setdefault(k.strip(), v)


def _expand(value: Any) -> Any:
    if isinstance(value, str):
        def sub(m: re.Match) -> str:
            return os.environ.get(m.group(1), m.group(2) or "")
        return _ENV_RE.sub(sub, value)
    if isinstance(value, dict):
        return {k: _expand(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_expand(v) for v in value]
    return value


def _merge(base: dict, override: dict) -> dict:
    out = dict(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = v
    return out


def load_config(path: str | Path = "config.yaml") -> dict[str, Any]:
    load_dotenv()
    p = Path(path)
    if not p.exists():
        example = p.with_name("config.example.yaml")
        if example.exists():
            p = example
        else:
            raise FileNotFoundError(f"{path} not found (and no config.example.yaml)")
    raw = yaml.safe_load(p.read_text()) or {}
    cfg = _merge(DEFAULTS, _expand(raw))
    cfg["_path"] = str(p)
    return cfg


def detector_config(cfg: dict[str, Any]) -> DetectorConfig:
    d = cfg.get("detector") or {}
    known = {k: v for k, v in d.items() if k in DetectorConfig.__dataclass_fields__}
    return DetectorConfig(**known)
