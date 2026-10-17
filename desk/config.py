"""Desk configuration. Everything comes from the environment; no secret lives in code.

The desk process must never see the Jev key: `assert_desk_cannot_see_jev_key` refuses to run if
TYPESAFE_API_KEY is present in its environment.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from judge.jev import JEV_KEY_ENV, STUB_MODEL, ModelNotPinnedError, ensure_pinned
from risk.limits import RiskLimits

MODES = ("shadow", "paper")
BOTS = ("gambler", "house", "spy")
FEEDS = ("synthetic", "replay")
MIN_DESK_SECRET_CHARS = 32


class ConfigError(ValueError):
    pass


def _get(env: Mapping[str, str], key: str, default: str) -> str:
    value = env.get(key)
    return default if value is None or not value.strip() else value.strip()


def _float(env: Mapping[str, str], key: str, default: str) -> float:
    try:
        return float(_get(env, key, default))
    except ValueError as exc:
        raise ConfigError(f"{key} must be a number") from exc


def _int(env: Mapping[str, str], key: str, default: str) -> int:
    try:
        return int(_get(env, key, default))
    except ValueError as exc:
        raise ConfigError(f"{key} must be an integer") from exc


def assert_desk_cannot_see_jev_key(env: Mapping[str, str]) -> None:
    if (env.get(JEV_KEY_ENV) or "").strip():
        raise ConfigError(f"{JEV_KEY_ENV} is visible to the desk process; bots must never hold the Jev key. Move it to the judge's environment.")


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


@dataclass(frozen=True)
class DeskConfig:
    mode: str
    bot: str
    symbols: tuple[str, ...]
    block_seconds: float
    feed: str
    replay_path: str | None
    judge_url: str
    desk_secret: str = field(repr=False)
    jev_model: str
    log_dir: str
    limits: RiskLimits
    fee_bps: float
    maker_fee_bps: float
    gas_usd: float
    paper_cash_usd: float
    paper_slippage_bps: float
    order_qty: float
    max_jev_candidates: int
    ret_windows_blocks: tuple[int, int, int]
    rv_window_blocks: int
    max_spread_bps: float
    rv_min_bps: float
    rv_max_bps: float
    min_ticks: int
    max_stale_ms: int
    max_feed_lag_ms: int
    min_equity_usd: float
    deadline_margin_frac: float
    warmup_blocks: int
    pending_order_ttl_blocks: int
    synthetic_seed: int
    synthetic_tick_ms: int

    @property
    def block_ms(self) -> int:
        return int(round(self.block_seconds * 1000))

    @property
    def judge_is_stub(self) -> bool:
        return self.judge_url.startswith("stub://")

    @classmethod
    def from_env(cls, env: Mapping[str, str], overrides: Mapping[str, str] | None = None) -> DeskConfig:
        env = {**env, **{k: v for k, v in (overrides or {}).items() if v is not None}}
        mode = _get(env, "DESK_MODE", "shadow")
        bot = _get(env, "DESK_BOT", "gambler")
        feed = _get(env, "FEED", "synthetic")
        if mode not in MODES:
            raise ConfigError(f"DESK_MODE must be one of {MODES}")
        if bot not in BOTS:
            raise ConfigError(f"DESK_BOT must be one of {BOTS}")
        if feed not in FEEDS:
            raise ConfigError(f"FEED must be one of {FEEDS}")
        symbols = tuple(s.strip() for s in _get(env, "DESK_SYMBOLS", "ETH-USD").split(",") if s.strip())
        if not symbols:
            raise ConfigError("DESK_SYMBOLS must list at least one symbol")
        block_seconds = _float(env, "BLOCK_SECONDS", "12")
        if block_seconds <= 0:
            raise ConfigError("BLOCK_SECONDS must be positive")
        block_ms = int(round(block_seconds * 1000))
        judge_url = _get(env, "JUDGE_URL", "stub://local")
        desk_secret = _get(env, "DESK_SECRET", "")
        is_stub = judge_url.startswith("stub://")
        if not is_stub and len(desk_secret) < MIN_DESK_SECRET_CHARS:
            raise ConfigError(f"DESK_SECRET must be at least {MIN_DESK_SECRET_CHARS} characters when JUDGE_URL is a real judge")
        jev_model = _get(env, "JEV_MODEL", STUB_MODEL if is_stub else "")
        try:
            jev_model = ensure_pinned(jev_model)
        except ModelNotPinnedError as exc:
            raise ConfigError(str(exc)) from exc
        fee_bps = _float(env, "FEE_BPS", "10")
        maker_fee_bps = _float(env, "MAKER_FEE_BPS", "2")
        gas_usd = _float(env, "GAS_USD", "0.05")
        try:
            limits = RiskLimits(
                max_position_units=_float(env, "MAX_POSITION_UNITS", "1.0"),
                max_notional_usd=_float(env, "MAX_NOTIONAL_USD", "5000"),
                daily_loss_limit_usd=_float(env, "DAILY_LOSS_LIMIT_USD", "100"),
                max_leverage=_float(env, "MAX_LEVERAGE", "1.0"),
                range_guard_bps=_float(env, "RANGE_GUARD_BPS", "50"),
                range_guard_ref_bps=_float(env, "RANGE_GUARD_REF_BPS", "300"),
                fee_bps=fee_bps,
                maker_fee_bps=maker_fee_bps,
                gas_usd=gas_usd,
                min_edge_margin=_float(env, "MIN_EDGE_MARGIN", "0.5"),
                pinned_model=jev_model,
                max_stale_ms=_int(env, "MAX_STALE_MS", str(2 * block_ms)),
            ).validate()
        except ValueError as exc:
            raise ConfigError(str(exc)) from exc
        windows = tuple(int(w) for w in _get(env, "RET_WINDOWS_BLOCKS", "1,5,20").split(","))
        if len(windows) != 3 or any(w <= 0 for w in windows):
            raise ConfigError("RET_WINDOWS_BLOCKS must be three positive integers")
        order_qty = _float(env, "ORDER_QTY", "0.2")
        if order_qty <= 0:
            raise ConfigError("ORDER_QTY must be positive")
        replay_path = _get(env, "FEED_REPLAY_PATH", "") or None
        if feed == "replay" and not replay_path:
            raise ConfigError("FEED=replay needs FEED_REPLAY_PATH")
        return cls(
            mode=mode,
            bot=bot,
            symbols=symbols,
            block_seconds=block_seconds,
            feed=feed,
            replay_path=replay_path,
            judge_url=judge_url,
            desk_secret=desk_secret,
            jev_model=jev_model,
            log_dir=_get(env, "LOG_DIR", "logs/data"),
            limits=limits,
            fee_bps=fee_bps,
            maker_fee_bps=maker_fee_bps,
            gas_usd=gas_usd,
            paper_cash_usd=_float(env, "PAPER_CASH_USD", "10000"),
            paper_slippage_bps=_float(env, "PAPER_SLIPPAGE_BPS", "1"),
            order_qty=order_qty,
            max_jev_candidates=_int(env, "MAX_JEV_CANDIDATES", "1"),
            ret_windows_blocks=windows,  # type: ignore[arg-type]
            rv_window_blocks=_int(env, "RV_WINDOW_BLOCKS", "20"),
            max_spread_bps=_float(env, "MAX_SPREAD_BPS", "20"),
            rv_min_bps=_float(env, "RV_MIN_BPS", "1"),
            rv_max_bps=_float(env, "RV_MAX_BPS", "500"),
            min_ticks=_int(env, "MIN_TICKS", "30"),
            max_stale_ms=limits.max_stale_ms,
            max_feed_lag_ms=_int(env, "MAX_FEED_LAG_MS", str(block_ms)),
            min_equity_usd=_float(env, "MIN_EQUITY_USD", "100"),
            deadline_margin_frac=_float(env, "DEADLINE_MARGIN_FRAC", "0.1"),
            warmup_blocks=_int(env, "WARMUP_BLOCKS", "25"),
            pending_order_ttl_blocks=_int(env, "PENDING_ORDER_TTL_BLOCKS", "3"),
            synthetic_seed=_int(env, "SYNTHETIC_SEED", "7"),
            synthetic_tick_ms=_int(env, "SYNTHETIC_TICK_MS", "1000"),
        )

    def public_dict(self) -> dict:
        data = {k: v for k, v in self.__dict__.items() if k != "desk_secret"}
        data["limits"] = self.limits.to_dict()
        data["desk_secret_set"] = bool(self.desk_secret)
        return data
