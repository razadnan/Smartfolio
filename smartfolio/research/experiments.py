import pandas as pd

from smartfolio.research.backtester import walk_forward
from smartfolio.research.config import load_config
from smartfolio.research.metrics import portfolio_summary
from smartfolio.portfolio.markowitz import max_sharpe as _max_sharpe, min_volatility as _min_vol
from smartfolio.portfolio.ledoit_wolf import ledoit_wolf_cov as _lw_cov, sample_cov as _sample_cov


import numpy as np


def _safe_max_sharpe(mu, cov):
    """Try max_sharpe(rf=0), fallback to min_vol, fallback to equal weight."""
    try:
        return _max_sharpe(mu, cov, rf=0.0)
    except (ValueError, RuntimeError):
        pass
    try:
        return _min_vol(mu, cov)
    except (ValueError, RuntimeError):
        pass
    import pandas as pd
    n = len(mu)
    return pd.Series(np.full(n, 1.0 / n), index=mu.index)


class _Opt:
    @staticmethod
    def max_sharpe(mu, cov, w_max=None): return _safe_max_sharpe(mu, cov)
    @staticmethod
    def lw_cov(r): return _lw_cov(r)[0]
    @staticmethod
    def sample_cov(r): return _sample_cov(r)

opt = _Opt()
PRED_COL = {"E3": "xgb_prediction", "E4": "lstm_prediction", "E5": "ensemble_prediction"}


def _lookback(h):
    return h.iloc[-load_config()["walk_forward"]["train_window_days"]:]


def e0(h, d):
    return pd.Series(1 / h.shape[1], index=h.columns)


def e1(h, d):   # historical mean + sample covariance
    r = _lookback(h)
    return opt.max_sharpe(r.mean(), opt.sample_cov(r))


def e2(h, d):   # historical mean + Ledoit-Wolf
    r = _lookback(h)
    return opt.max_sharpe(r.mean(), opt.lw_cov(r))


def forecast_strategy(preds, col):
    """ML forecast (Student 1) + Ledoit-Wolf + optimizer."""
    table = preds.pivot(index="date", columns="symbol", values=col)
    horizon = load_config()["forecast_horizon_days"]

    def strat(h, d):
        if d not in table.index:
            raise ValueError(f"No predictions for {d.date()}")
        mu = table.loc[d].reindex(h.columns)
        if mu.isna().any():
            raise ValueError(f"Missing predictions on {d.date()}: {list(mu[mu.isna()].index)}")
        r = _lookback(h)
        return opt.max_sharpe(mu / horizon, opt.lw_cov(r))

    return strat


EXPERIMENTS = {"E0": e0, "E1": e1, "E2": e2}


def build_strategy(name, preds=None):
    if name in EXPERIMENTS:
        return EXPERIMENTS[name]
    if name in PRED_COL:
        if preds is None:
            raise ValueError(f"{name} needs a predictions DataFrame")
        return forecast_strategy(preds, PRED_COL[name])
    raise ValueError(f"Unknown experiment {name} (E6 is added in Block 8)")


def run_experiment(name, returns, preds=None, **kw):
    res = walk_forward(returns, build_strategy(name, preds), **kw)
    res["experiment"] = name
    res["summary"] = portfolio_summary(res["net"], res["weights"])
    res["summary"]["turnover"] = float(res["turnover"].iloc[1:].mean())
    res["summary_gross"] = portfolio_summary(res["gross"])
    return res

def model_strategy(model):
    """Strategy from any model with .predict(history, date) -> Series of horizon forecasts."""
    horizon = load_config()["forecast_horizon_days"]

    def strat(h, d):
        mu = model.predict(h, d).reindex(h.columns)
        if mu.isna().any():
            raise ValueError(f"Missing forecasts on {d.date()}")
        return opt.max_sharpe(mu / horizon, opt.lw_cov(_lookback(h)))

    return strat