import numpy as np
import pandas as pd

from smartfolio.research.backtester import walk_forward
from smartfolio.research.config import load_config
from smartfolio.research.metrics import portfolio_summary
from smartfolio.portfolio.markowitz import max_sharpe as _max_sharpe, min_volatility as _min_vol
from smartfolio.portfolio.ledoit_wolf import ledoit_wolf_cov as _lw_cov, sample_cov as _sample_cov


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


def e7(h, d):   # Hierarchical Risk Parity (HRP)
    r = _lookback(h)
    cov = opt.lw_cov(r)
    from smartfolio.portfolio.hrp import hrp_portfolio
    return hrp_portfolio(cov)


def e8(h, d):   # Black-Litterman model with market equilibrium views
    r = _lookback(h)
    cov = opt.lw_cov(r)
    from smartfolio.portfolio.black_litterman import black_litterman
    mu_bl = black_litterman(cov, r.mean())
    return opt.max_sharpe(mu_bl, cov)


def forecast_strategy(preds, col):
    """ML forecast + Ledoit-Wolf + optimizer."""
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


def uncertainty_strategy(preds, col="ensemble_prediction", penalty_lambda=1.5):
    """ML forecast penalized for forecast uncertainty (epistemic risk)."""
    table = preds.pivot(index="date", columns="symbol", values=col)
    horizon = load_config()["forecast_horizon_days"]
    from smartfolio.portfolio.robust import uncertainty_aware_mu

    def strat(h, d):
        if d not in table.index:
            raise ValueError(f"No predictions for {d.date()}")
        mu = table.loc[d].reindex(h.columns)
        if mu.isna().any():
            raise ValueError(f"Missing predictions on {d.date()}: {list(mu[mu.isna()].index)}")
        r = _lookback(h)
        mu_adj = uncertainty_aware_mu(mu / horizon, returns_df=r, penalty_lambda=penalty_lambda)
        return opt.max_sharpe(mu_adj, opt.lw_cov(r))

    return strat


def regime_strategy(preds, col="ensemble_prediction"):
    """Regime-switching: CVaR minimization during elevated volatility, Max Sharpe in calm markets."""
    table = preds.pivot(index="date", columns="symbol", values=col)
    horizon = load_config()["forecast_horizon_days"]
    from smartfolio.portfolio.cvar import min_cvar_portfolio

    def strat(h, d):
        if d not in table.index:
            raise ValueError(f"No predictions for {d.date()}")
        mu = table.loc[d].reindex(h.columns)
        r = _lookback(h)
        recent_vol = r.tail(21).mean(axis=1).std() * np.sqrt(252)
        long_vol = r.mean(axis=1).std() * np.sqrt(252)
        if recent_vol > long_vol * 1.20:
            return min_cvar_portfolio(r, alpha=0.95, w_max=load_config()["portfolio"]["w_max"])
        cov = opt.lw_cov(r)
        return opt.max_sharpe(mu / horizon, cov)

    return strat


EXPERIMENTS = {"E0": e0, "E1": e1, "E2": e2, "E7": e7, "E8": e8}


def build_strategy(name, preds=None):
    if name in EXPERIMENTS:
        return EXPERIMENTS[name]
    if name in PRED_COL:
        if preds is None:
            raise ValueError(f"{name} needs a predictions DataFrame")
        return forecast_strategy(preds, PRED_COL[name])
    if name in ("E9", "E9_xgb"):
        if preds is None: raise ValueError("E9 needs predictions")
        return forecast_strategy(preds, "xgb_prediction")
    if name == "E9_lstm":
        if preds is None: raise ValueError("E9_lstm needs predictions")
        return forecast_strategy(preds, "lstm_prediction")
    if name == "E10":
        if preds is None: raise ValueError("E10 needs predictions")
        return forecast_strategy(preds, "ensemble_prediction")
    if name == "E11":
        if preds is None: raise ValueError("E11 needs predictions")
        return uncertainty_strategy(preds, "ensemble_prediction", penalty_lambda=1.5)
    if name == "E12":
        if preds is None: raise ValueError("E12 needs predictions")
        return regime_strategy(preds, "ensemble_prediction")
    raise ValueError(f"Unknown experiment {name}")


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
