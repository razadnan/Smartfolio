"""TEMPORARY stand-ins for Student 2's module. Replace via the import in experiments.py."""
import numpy as np
import pandas as pd


from scipy.optimize import minimize
from sklearn.covariance import LedoitWolf

from smartfolio.research.config import load_config

from smartfolio.research.feedback import forward_returns


def sample_cov(r):
    return r.cov()


def lw_cov(r):
    c = LedoitWolf().fit(r.values).covariance_
    return pd.DataFrame(c, index=r.columns, columns=r.columns)


def max_sharpe(mu, cov, w_max=None):
    w_max = load_config()["portfolio"]["w_max"] if w_max is None else w_max
    m, S, n = mu.values, cov.values, len(mu)

    def neg_sharpe(w):
        v = np.sqrt(w @ S @ w)
        return -(w @ m) / v if v > 0 else 0.0

    res = minimize(neg_sharpe, np.full(n, 1 / n), method="SLSQP",
                   bounds=[(0, w_max)] * n,
                   constraints={"type": "eq", "fun": lambda w: w.sum() - 1})
    if not res.success:
        raise RuntimeError(f"Optimizer failed: {res.message}")
    return pd.Series(np.clip(res.x, 0, None), index=mu.index)

class MomentumModel:
    """Stand-in forecaster (Student 1's real models replace this)."""

    def __init__(self, lookback, version, scale=1.0, noise=0.0):
        self.lookback, self.version, self.scale, self.noise = lookback, version, scale, noise

    def predict(self, history, date):
        h = load_config()["forecast_horizon_days"]
        p = history.iloc[-self.lookback:].mean() * h * self.scale
        if self.noise:
            rng = np.random.default_rng(int(pd.Timestamp(date).strftime("%Y%m%d")))
            p = p + rng.normal(0, self.noise, len(p))
        return p


def train_momentum(train_returns, version):
    """Picks the lookback with the lowest in-sample forecast error."""
    h = load_config()["forecast_horizon_days"]
    fwd = forward_returns(train_returns, h)
    best = None
    for lb in (10, 20, 40, 60):
        err = float(np.nanmean(((train_returns.rolling(lb).mean() * h - fwd) ** 2).values))
        if best is None or err < best[0]:
            best = (err, lb)
    return MomentumModel(best[1], version)