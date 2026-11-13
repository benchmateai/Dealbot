"""Spy: information and regime watcher. Detects anomalies, regime shifts and large players; trades
only on a clear directional read with low danger.

Two questions (anomaly, edge_type) have no price-path outcome and are logged for review only.
"""

from questions.schema import OTHER_TEXT, Battery, ChoiceQ, NoulQ, Resolution, ScoreQ

BATTERY = Battery(
    bot="spy",
    questions=(
        NoulQ(
            "anomaly",
            "Does `mkt` show a data anomaly, such as a stale, crossed, or implausible quote, rather than a real market state?",
            true="The quote is not trustworthy as a description of the market.",
            false="The quote is a plausible, fresh market state.",
        ),
        NoulQ(
            "regime_shift",
            "Will the volatility regime over the next 20 blocks differ from the one `mkt.rv_bps` describes?",
            true="Realized volatility over the next 20 blocks is above one and a half times or below half of `mkt.rv_bps`.",
            false="Realized volatility stays between half and one and a half times `mkt.rv_bps`.",
            resolution=Resolution(rule="vol_regime_differs", horizon_blocks=20, param="rv"),
        ),
        NoulQ(
            "large_player",
            "Is a large participant moving the book, as an extreme `mkt.imb` together with a widening `mkt.spr_bps` would suggest?",
            true="`mkt.mid` ends more than twice `desk.cost_bps` away from its current level after 10 blocks.",
            false="It does not.",
            resolution=Resolution(rule="abs_end_above", horizon_blocks=10, param="2cost"),
        ),
        ChoiceQ(
            "edge_type",
            "Which exploitable information asymmetry, if any, is present in `mkt`?",
            criteria={
                "momentum_ignition": "A fast one-sided push in `mkt.ret_bps.w1` with thin depth on the opposite side.",
                "liquidity_gap": "Depth on one side is far smaller than on the other, so a small order would move `mkt.mid`.",
                "stale_quote": "The quote has not kept up with the recent moves in `mkt.ret_bps`.",
                "none": "No exploitable asymmetry is present.",
                "other": OTHER_TEXT,
            },
        ),
        ScoreQ(
            "danger",
            "How dangerous is it to hold a position in `mkt` over the next 20 blocks?",
            levels=(
                "Safe: the move over 20 blocks stays within `desk.cost_bps`.",
                "Caution: the move is between one and two times `desk.cost_bps`.",
                "Stand aside: the move is between two and four times `desk.cost_bps`.",
                "Halt: the move is more than four times `desk.cost_bps`.",
            ),
            resolution=Resolution(rule="danger_level", horizon_blocks=20, param="cost"),
        ),
        ChoiceQ(
            "dir_if_any",
            "Over the next 20 blocks, in which direction does `mkt.mid` first move by more than `desk.cost_bps`?",
            criteria={
                "up": "`mkt.mid` rises by more than `desk.cost_bps` before it falls by that much.",
                "down": "`mkt.mid` falls by more than `desk.cost_bps` before it rises by that much.",
                "flat": "Neither move exceeds `desk.cost_bps` within 20 blocks.",
                "other": OTHER_TEXT,
            },
            resolution=Resolution(rule="direction_first_touch", horizon_blocks=20, param="cost"),
        ),
        NoulQ(
            "stale_next",
            "Will `mkt.mid` be more than `desk.cost_bps` away from its current level by the next block?",
            true="`mkt.mid` moves by more than `desk.cost_bps` within one block.",
            false="It stays within `desk.cost_bps`.",
            resolution=Resolution(rule="abs_end_above", horizon_blocks=1, param="cost"),
        ),
        NoulQ(
            "exit_now",
            "Given `pos` and `mkt`, should the open position be closed now rather than held for 10 more blocks?",
            true="Holding 10 more blocks loses more than `desk.cost_bps` against the position.",
            false="Holding 10 more blocks does not lose that much.",
            resolution=Resolution(rule="pos_loses_more_than", horizon_blocks=10, param="cost"),
        ),
    ),
)
