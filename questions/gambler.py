"""Gambler: momentum and breakout hunter. Wants asymmetric payoffs and accepts being wrong often.

State sent with every battery: {"mkt": snapshot, "pos": open position or null, "desk": {bot, phase,
cost_bps, fee_bps, gas_usd}}. Thresholds and combination weights live in policy/, not here.
Position questions are asked every time (full battery, one call); they resolve as unresolvable when flat.
"""

from questions.schema import OTHER_TEXT, Battery, ChoiceQ, NoulQ, Resolution

BATTERY = Battery(
    bot="gambler",
    questions=(
        ChoiceQ(
            "dir_20",
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
            "continuation",
            "Will the move shown in `mkt.ret_bps.w5` continue in the same direction by more than `desk.cost_bps` over the next 20 blocks?",
            true="The next 20 blocks extend the `w5` move by more than `desk.cost_bps` before reversing by that much.",
            false="The move stalls or reverses first.",
            resolution=Resolution(rule="continues_w5", horizon_blocks=20, param="cost"),
        ),
        NoulQ(
            "late_entry",
            "Has the move in `mkt.ret_bps` already run its course, so that entering now would be chasing?",
            true="The next 20 blocks first reverse against the `w5` direction by more than `desk.cost_bps`.",
            false="The move has room left: it extends before it reverses.",
            resolution=Resolution(rule="against_w5_first", horizon_blocks=20, param="cost"),
        ),
        NoulQ(
            "whipsaw",
            "Will `mkt.mid` move by more than `desk.cost_bps` in both directions within the next 20 blocks?",
            true="Both an up move and a down move larger than `desk.cost_bps` occur within 20 blocks.",
            false="At most one direction moves that much.",
            resolution=Resolution(rule="touches_both", horizon_blocks=20, param="cost"),
        ),
        ChoiceQ(
            "regime",
            "Which regime best describes what `mkt` will do over the next 20 blocks?",
            criteria={
                "trending": "`mkt.mid` ends more than twice `desk.cost_bps` away from its start, without first moving that far both ways.",
                "ranging": "`mkt.mid` stays within twice `desk.cost_bps` of its start the whole time.",
                "volatile_chop": "`mkt.mid` moves more than twice `desk.cost_bps` in both directions.",
                "other": OTHER_TEXT,
            },
            resolution=Resolution(rule="regime_realized", horizon_blocks=20, param="cost"),
        ),
        NoulQ(
            "thesis_broken",
            "Given `pos` and `mkt`, is the open position's thesis already invalidated?",
            true="Holding for 10 more blocks loses more than `desk.cost_bps` against the position.",
            false="The position does not lose that much over the next 10 blocks.",
            resolution=Resolution(rule="pos_loses_more_than", horizon_blocks=10, param="cost"),
        ),
        NoulQ(
            "keep_running",
            "Will the open position's unrealized PnL be higher 10 blocks from now than it is now?",
            true="The price moves in the position's favor over the next 10 blocks.",
            false="It does not.",
            resolution=Resolution(rule="pos_gains", horizon_blocks=10, param=0),
        ),
    ),
)
