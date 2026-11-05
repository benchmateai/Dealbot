"""Kalshi: a binary contract on an underlying's price at expiry. The baseline probability comes from a
formula in code (kalshi/model.py); these questions ask only what the formula misses: whether the quote
is stale, where the underlying is heading in the minutes left, and how violent the path will be.

State: {"mkt": the contract's own YES price snapshot, "contract": {ticker, strike, expires_in_s, yes_bid,
yes_ask, spot, distance_bps, model_p_yes, underlying_snapshot}, "pos": open position or null, "desk": {...}}.
"""

from questions.schema import OTHER_TEXT, Battery, ChoiceQ, NoulQ, Resolution, ScoreQ

BATTERY = Battery(
    bot="kalshi",
    questions=(
        NoulQ(
            "settles_yes",
            "Will `contract` settle YES, with `contract.spot` ending above `contract.strike` when `contract.expires_in_s` runs out?",
            true="The underlying's price at expiry is above `contract.strike`.",
            false="It is at or below `contract.strike`.",
            resolution=Resolution(rule="end_price_above_half", horizon_blocks="expiry", param=0),
        ),
        NoulQ(
            "pickoff",
            "Is `contract.yes_ask` stale against `contract.spot` and `mkt`, so that a buyer at the ask would be picked off within a minute?",
            true="The contract's YES price falls by more than one and a half percent within the next five blocks.",
            false="It does not.",
            resolution=Resolution(rule="end_below", horizon_blocks=5, param=150),
        ),
        ChoiceQ(
            "momentum",
            "Over the time left in `contract`, does `contract.spot` move toward `contract.strike`, away from it, or stay?",
            criteria={
                "toward": "`contract.spot` moves more than 5 bps toward `contract.strike` by expiry.",
                "away": "`contract.spot` moves more than 5 bps away from `contract.strike` by expiry.",
                "stay": "`contract.spot` ends within 5 bps of where it is now.",
                "other": OTHER_TEXT,
            },
            resolution=Resolution(rule="moves_toward_strike", horizon_blocks="expiry", param=5, on="underlying"),
        ),
        ScoreQ(
            "danger",
            "How far will `contract.spot` have moved, in either direction, when `contract` expires?",
            levels=(
                "Within 20 bps of where it is now.",
                "Between 20 and 40 bps away.",
                "Between 40 and 80 bps away.",
                "More than 80 bps away.",
            ),
            resolution=Resolution(rule="danger_level", horizon_blocks="expiry", param=20, on="underlying"),
        ),
        NoulQ(
            "exit_now",
            "Given `pos` and `contract`, should the position be closed now at the current price rather than held to settlement?",
            true="Holding to settlement loses more than three percent of the contract price against the position.",
            false="Holding does not lose that much.",
            resolution=Resolution(rule="pos_loses_more_than", horizon_blocks="expiry", param=300),
        ),
    ),
)
