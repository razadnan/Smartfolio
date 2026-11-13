"""Historical return calculations and annualization helpers."""
import numpy as np
import pandas as pd
from configs.config import TRADING_DAYS


def compute_returns(prices: pd.DataFrame, log: bool = False) -> pd.DataFrame:
    """Daily returns from a price matrix (index=date, columns=symbol)."""
    if prices.empty:
        raise ValueError("Price matrix is empty.")
    prices = prices.sort_index()
    if (prices <= 0).any().any():
        raise ValueError("Prices must be strictly positive.")
    if log:
        rets = np.log(prices / prices.shift(1))
    else:
        rets = prices.pct_change()
    return rets.iloc[1:].dropna(how="all")


def clean_returns(returns: pd.DataFrame, min_obs: int = 60) -> pd.DataFrame:
    """Drop symbols with too little history, then drop rows with any NaN."""
    valid = returns.columns[returns.notna().sum() >= min_obs]
    out = returns[valid].dropna()
    if out.shape[1] < 2:
        raise ValueError("Need at least 2 assets with sufficient history.")
    if not np.isfinite(out.values).all():
        raise ValueError("Returns contain NaN/Inf.")
    return out


def historical_mean_returns(returns: pd.DataFrame) -> pd.Series:
    """Annualized historical mean return (used by E1/E2 baselines)."""
    return returns.mean() * TRADING_DAYS


def annualized_volatility(returns: pd.DataFrame) -> pd.Series:
    return returns.std() * np.sqrt(TRADING_DAYS)


def predictions_to_mu(pred_df: pd.DataFrame, date, horizon_days: int = 5,
                      col: str = "ensemble_prediction") -> pd.Series:
    """
    Convert Student 1's predictions for one date into an annualized
    expected-return vector. Assumes prediction = return over `horizon_days`.
    """
    d = pred_df[pd.to_datetime(pred_df["date"]) == pd.to_datetime(date)]
    if d.empty:
        raise ValueError(f"No predictions for date {date}.")
    if d["symbol"].duplicated().any():
        raise ValueError("Duplicate symbols in predictions.")
    mu = d.set_index("symbol")[col].astype(float)
    if not np.isfinite(mu.values).all():
        raise ValueError("Predictions contain NaN/Inf.")
    return mu * (TRADING_DAYS / horizon_days)


def predictive_alpha_returns(hist_returns: pd.DataFrame, risk_profile: str = "Moderate") -> pd.Series:
    """
    Dynamic multi-factor expected returns blending:
      - 20-day medium-term momentum
      - 60-day EMA trend
      - Mean-reversion factor
      - Long-term mean baseline
      - Risk profile weighting
    """
    if hist_returns.empty:
        raise ValueError("Historical returns dataframe is empty.")
    n_days = len(hist_returns)
    lookback_mom = min(20, n_days)
    lookback_rev = min(5, n_days)

    cum_20 = (1.0 + hist_returns.tail(lookback_mom)).prod() - 1.0
    cum_5 = (1.0 + hist_returns.tail(lookback_rev)).prod() - 1.0
    ema_trend = hist_returns.ewm(span=min(60, n_days), min_periods=min(10, n_days)).mean().iloc[-1]
    long_mean = hist_returns.mean()

    # Alpha signals per day
    alpha_daily = (0.35 * (cum_20 / float(lookback_mom))
                   + 0.35 * ema_trend
                   + 0.30 * long_mean
                   - 0.05 * (cum_5 / float(lookback_rev)))

    rf_weight = {"Conservative": 0.25, "Moderate": 0.50, "Aggressive": 0.85}.get(risk_profile, 0.50)
    rf_daily = 0.06 / 252.0
    return alpha_daily * rf_weight + rf_daily * (1.0 - rf_weight)
