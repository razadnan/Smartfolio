import numpy as np
import pandas as pd

from smartfolio.research.config import load_config

_cfg = load_config()
PPY = _cfg["periods_per_year"]
RF = _cfg["risk_free_rate"]


# ---------- prediction metrics ----------
def mae(y, p):
    y, p = np.asarray(y, float), np.asarray(p, float)
    return float(np.mean(np.abs(y - p)))


def rmse(y, p):
    y, p = np.asarray(y, float), np.asarray(p, float)
    return float(np.sqrt(np.mean((y - p) ** 2)))


def r2(y, p):
    y, p = np.asarray(y, float), np.asarray(p, float)
    ss_tot = np.sum((y - y.mean()) ** 2)
    return float(1 - np.sum((y - p) ** 2) / ss_tot) if ss_tot else np.nan


def directional_accuracy(y, p):
    y, p = np.asarray(y, float), np.asarray(p, float)
    return float(np.mean(np.sign(y) == np.sign(p)))


# ---------- portfolio metrics (r = periodic simple returns) ----------
def annual_return(r, ppy=PPY):
    r = pd.Series(r).dropna()
    return float((1 + r).prod() ** (ppy / len(r)) - 1)


def annual_vol(r, ppy=PPY):
    return float(pd.Series(r).dropna().std(ddof=1) * np.sqrt(ppy))


def sharpe(r, rf=RF, ppy=PPY):
    r = pd.Series(r).dropna()
    ex = r - rf / ppy
    sd = ex.std(ddof=1)
    return float(ex.mean() / sd * np.sqrt(ppy)) if sd > 0 else np.nan


def sortino(r, rf=RF, ppy=PPY):
    r = pd.Series(r).dropna()
    ex = r - rf / ppy
    dd = np.sqrt(np.mean(np.minimum(ex, 0) ** 2))
    return float(ex.mean() / dd * np.sqrt(ppy)) if dd > 0 else np.nan


def max_drawdown(r):
    w = (1 + pd.Series(r).dropna()).cumprod()
    return float((w / w.cummax() - 1).min())


def calmar(r, ppy=PPY):
    mdd = abs(max_drawdown(r))
    return annual_return(r, ppy) / mdd if mdd > 0 else np.nan


def turnover_series(weights):
    """weights: DataFrame (rebalance dates x symbols). One-way turnover
    per rebalance = sum|w_t - w_{t-1}| / 2. First row = initial build from cash."""
    w = weights.fillna(0.0)
    prev = w.shift(1).fillna(0.0)
    return (w - prev).abs().sum(axis=1) / 2

def avg_turnover(weights):
    """Mean one-way turnover per rebalance, excluding the initial build."""
    return float(turnover_series(weights).iloc[1:].mean())


def portfolio_summary(r, weights=None):
    out = {
        "annual_return": annual_return(r),
        "volatility": annual_vol(r),
        "sharpe": sharpe(r),
        "sortino": sortino(r),
        "calmar": calmar(r),
        "max_drawdown": max_drawdown(r),
    }
    if weights is not None:
        out["turnover"] = avg_turnover(weights)
    return out