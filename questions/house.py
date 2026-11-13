"""House: the casino. Passive quotes, mean reversion, small edge over fees, avoids informed flow.

Same state shape as every bot. Entry orders are passive limits at the touch; the policy in policy/
turns these judgments into a quote-side decision.
"""

from questions.schema import OTHER_TEXT, Battery, ChoiceQ, NoulQ, Resolution, ScoreQ

BATTERY = Battery(
    bot="house",
    questions=(
        NoulQ(
            "spread_edge",
            "Over the next 10 blocks, will a passive fill at the current bid or ask earn more than `desk.cost_bps` after fees and gas?",
            true="`mkt.mid` stays within `desk.cost_bps` of its current level for 10 blocks, so a resting quote earns the spread without being run over.",
            false="`mkt.mid` moves by more than `desk.cost_bps` in either direction within 10 blocks.",
            resolution=Resolution(rule="range_bound", horizon_blocks=10, param="cost"),
        ),
        NoulQ(
            "informed_flow",
            "Does `mkt.imb` signal informed flow that will push `mkt.mid` through the heavier side of the book within 10 blocks?",
            true="`mkt.mid` first moves by more than `desk.cost_bps` in the direction `mkt.imb` points (positive means up).",
            false="It does not move that way first.",
            resolution=Resolution(rule="with_imbalance_first", horizon_blocks=10, param="cost"),
        ),
        ChoiceQ(
            "revert_10",
            "Over the next 10 blocks, does `mkt.mid` revert toward where it was 20 blocks ago, continue away from it, or stay put?",
            criteria={
                "revert": "`mkt.mid` moves by more than `desk.cost_bps` against the sign of `mkt.ret_bps.w20`.",
                "continue": "`mkt.mid` moves by more than `desk.cost_bps` in the same direction as `mkt.ret_bps.w20`.",
                "stay": "`mkt.mid` ends within `desk.cost_bps` of its current level.",
                "other": OTHER_TEXT,
            },
            resolution=Resolution(rule="revert_or_continue", horizon_blocks=10, param="cost"),
        ),
        ScoreQ(
            "vol_next",
            "How volatile will `mkt` be over the next 20 blocks relative to `mkt.rv_bps`?",
            levels=(
                "Calm: realized volatility below half of `mkt.rv_bps`.",
                "Normal: realized volatility between half and one and a half times `mkt.rv_bps`.",
                "Elevated: realized volatility between one and a half and three times `mkt.rv_bps`.",
                "Extreme: realized volatility more than three times `mkt.rv_bps`.",
            ),
            resolution=Resolution(rule="vol_level", horizon_blocks=20, param="rv"),
        ),
        NoulQ(
            "toxic_tape",
            "Is the recent tape one-directional and informed, so that a passive quote would be picked off?",
            true="`mkt.mid` ends more than twice `desk.cost_bps` away from its current level after 10 blocks.",
            false="It ends within twice `desk.cost_bps`.",
            resolution=Resolution(rule="abs_end_above", horizon_blocks=10, param="2cost"),
        ),
        ChoiceQ(
            "lean_side",
            "Which side should a market maker quote more aggressively right now?",
            criteria={
                "bid": "Buying is right: `mkt.mid` first rises by more than `desk.cost_bps`.",
                "ask": "Selling is right: `mkt.mid` first falls by more than `desk.cost_bps`.",
                "both": "Quote both sides: `mkt.mid` stays within `desk.cost_bps` for 10 blocks.",
                "neither": "Pull quotes: `mkt.mid` moves by more than `desk.cost_bps` in both directions.",
                "other": OTHER_TEXT,
            },
            resolution=Resolution(rule="lean_realized", horizon_blocks=10, param="cost"),
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
