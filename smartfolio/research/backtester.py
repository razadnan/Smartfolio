import numpy as np
import pandas as pd

from smartfolio.research.config import load_config
from smartfolio.research.transaction_costs import rebalance_cost


def validate_weights(w, w_max=None, tol=1e-6):
    w = pd.Series(w, dtype=float)
    w_max = load_config()["portfolio"]["w_max"] if w_max is None else w_max
    if w.isna().any() or np.isinf(w).any():
        raise ValueError("Weights contain NaN/Inf")
    if (w < -tol).any():
        raise ValueError("Negative weight (short selling not allowed)")
    if abs(w.sum() - 1) > tol:
        raise ValueError(f"Weights sum to {w.sum():.6f}, expected 1")
    if (w > w_max + tol).any():
        raise ValueError(f"Weight above cap {w_max}")
    return w.clip(lower=0)


def walk_forward(returns, strategy, train_window=None, rebalance_days=None, costs=None):
    """
    returns : DataFrame (dates x symbols) of daily simple returns.
    strategy: f(history_df, decision_date) -> weights {symbol: w}.
              history_df holds ONLY rows up to and including decision_date.
    Returns dict: gross, net (Series), weights (DataFrame), costs (Series).
    """
    cfg = load_config()["walk_forward"]
    tw = train_window or cfg["train_window_days"]
    rb = rebalance_days or cfg["rebalance_days"]
    if len(returns) <= tw:
        raise ValueError("Not enough data for the training window")

    gross_parts, net_parts, w_rows, c_rows, t_rows = [], [], {}, {}, {}
    prev = pd.Series(0.0, index=returns.columns)  # start in cash

    for i in range(tw, len(returns), rb):
        d = returns.index[i - 1]
        w = validate_weights(strategy(returns.iloc[:i], d))
        w = w.reindex(returns.columns).fillna(0.0)
        t_rows[d] = float((w - prev).abs().sum() / 2)  # actual one-way trade size
        cost = rebalance_cost(prev, w, costs)

        block = returns.iloc[i:i + rb].fillna(0.0)
        growth = (1 + block).cumprod() * w          # value of each holding
        value = growth.sum(axis=1)
        g = value.pct_change()
        g.iloc[0] = value.iloc[0] - 1
        n = g.copy()
        n.iloc[0] = (1 + g.iloc[0]) * (1 - cost) - 1

        prev = growth.iloc[-1] / value.iloc[-1]     # drifted end-of-period weights
        gross_parts.append(g)
        net_parts.append(n)
        w_rows[d] = w
        c_rows[d] = cost

    return {
        "gross": pd.concat(gross_parts),
        "net": pd.concat(net_parts),
        "weights": pd.DataFrame(w_rows).T,
        "costs": pd.Series(c_rows),
        "turnover": pd.Series(t_rows),
    }
