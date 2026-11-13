import pandas as pd

from smartfolio.research.config import load_config


def _rates(c):
    fees = c["brokerage"] + c["exchange_txn"] + c["sebi"]
    gst = c["gst"] * fees
    buy = c["stt"] + c["stamp_duty_buy"] + fees + gst
    sell = c["stt"] + fees + gst
    return buy, sell


def rebalance_cost(prev_w, new_w, costs=None):
    """Cost as a fraction of portfolio value for moving prev_w -> new_w.
    prev_w / new_w: dict or Series {symbol: weight}. Pass drifted prev weights."""
    c = costs or load_config()["costs"]
    buy, sell = _rates(c)
    d = pd.Series(new_w, dtype=float).sub(pd.Series(prev_w, dtype=float), fill_value=0.0)
    return float(d.clip(lower=0).sum() * buy + (-d.clip(upper=0)).sum() * sell)


def cost_series(weights, costs=None):
    """weights: DataFrame (rebalance dates x symbols), no drift.
    First row is built from cash."""
    w = weights.fillna(0.0)
    prev = w.shift(1).fillna(0.0)
    return pd.Series(
        [rebalance_cost(prev.loc[i], w.loc[i], costs) for i in w.index],
        index=w.index,
    )


def cost_assumptions():
    """Record these next to every result."""
    return dict(load_config()["costs"])