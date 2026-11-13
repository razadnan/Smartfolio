import numpy as np
import pandas as pd


def make_returns(n_days=1000, n_assets=8, seed=42):
    """Synthetic daily returns for development. Never use for official results."""
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2020-01-01", periods=n_days)
    cols = [f"S{i}" for i in range(n_assets)]
    mu = rng.normal(0.0004, 0.0003, n_assets)
    sd = rng.uniform(0.01, 0.02, n_assets)
    return pd.DataFrame(rng.normal(mu, sd, (n_days, n_assets)), index=idx, columns=cols)

def make_predictions(returns, horizon=5, window=20):
    """Fake Student-1-style predictions for development only."""
    p = (returns.rolling(window).mean() * horizon).stack().dropna()
    df = p.rename("xgb_prediction").reset_index()
    df.columns = ["date", "symbol", "xgb_prediction"]
    df["lstm_prediction"] = df["xgb_prediction"] * 0.9
    df["ensemble_prediction"] = (df["xgb_prediction"] + df["lstm_prediction"]) / 2
    df["model_version"] = "mock"
    return df