import numpy as np
import pandas as pd

from smartfolio.research import metrics as m
from smartfolio.research.config import load_config


def forward_returns(returns, horizon=None):
    """Compounded return over the next `horizon` days, aligned at decision date t."""
    h = horizon or load_config()["forecast_horizon_days"]
    cum = (1 + returns.fillna(0)).cumprod()
    return cum.shift(-h) / cum - 1


def prediction_feedback(preds, returns, col="ensemble_prediction", horizon=None):
    """Prediction vs realised outcome. `known_by` = first date the outcome is observable."""
    h = horizon or load_config()["forecast_horizon_days"]
    fwd = forward_returns(returns, h).stack().rename("actual").reset_index()
    fwd.columns = ["date", "symbol", "actual"]
    known = pd.Series(returns.index[h:], index=returns.index[:-h])

    df = (preds[["date", "symbol", col]]
          .rename(columns={col: "prediction"})
          .merge(fwd, on=["date", "symbol"])
          .dropna(subset=["actual"]))
    df["known_by"] = df["date"].map(known)
    df = df.dropna(subset=["known_by"]).copy()
    df["error"] = df["prediction"] - df["actual"]
    df["abs_error"] = df["error"].abs()
    df["direction_correct"] = np.sign(df["prediction"]) == np.sign(df["actual"])
    df["model_col"] = col
    return df.reset_index(drop=True)


def feedback_as_of(fb, as_of):
    """Only feedback whose outcome was already known at `as_of` (leakage guard)."""
    return fb[fb["known_by"] <= as_of]


def portfolio_feedback(weights, net):
    """Realised outcome of each allocation over its holding period."""
    dates, rows = list(weights.index), []
    for i, d in enumerate(dates):
        mask = net.index > d
        if i + 1 < len(dates):
            mask &= net.index <= dates[i + 1]
        sel = net[mask]
        if sel.empty:
            continue
        rows.append({
            "date": d,
            "period_end": sel.index[-1],
            "realized_return": float((1 + sel).prod() - 1),
            "realized_sharpe": m.sharpe(sel),
            "realized_max_drawdown": m.max_drawdown(sel),
            "known_by": sel.index[-1],
        })
    return pd.DataFrame(rows)


class FeedbackTracker:
    """Retrain when >= every_days trading days passed AND >= min_feedback_obs
    new observation dates accumulated since the last retrain."""

    def __init__(self, last_retrain=None):
        self.cfg = load_config()["retraining"]
        self.last_retrain = last_retrain

    def check(self, fb, as_of, trading_dates):
        known = feedback_as_of(fb, as_of)
        if self.last_retrain is not None:
            known = known[known["known_by"] > self.last_retrain]
            td = pd.DatetimeIndex(trading_dates)
            days = int(((td > self.last_retrain) & (td <= as_of)).sum())
        else:
            days = None   # never retrained: cadence condition satisfied
        n_obs = int(known["known_by"].nunique())
        ok_days = days is None or days >= self.cfg["every_days"]
        ok_obs = n_obs >= self.cfg["min_feedback_obs"]
        if ok_days and ok_obs:
            reason = "cadence and minimum feedback both met"
        elif not ok_days:
            reason = f"only {days} trading days since last retrain"
        else:
            reason = f"only {n_obs} new feedback observations"
        return {"retrain": bool(ok_days and ok_obs), "days_since": days,
                "n_new_obs": n_obs, "reason": reason}

    def mark_retrained(self, as_of):
        self.last_retrain = as_of