import numpy as np
import pandas as pd
import pytest
from smartfolio.portfolio.returns import compute_returns, clean_returns, predictions_to_mu


def _prices():
    idx = pd.date_range("2024-01-01", periods=100, freq="B")
    rng = np.random.default_rng(42)
    p = 100 * np.exp(np.cumsum(rng.normal(0, 0.01, (100, 3)), axis=0))
    return pd.DataFrame(p, index=idx, columns=["A", "B", "C"])


def test_returns_shape():
    r = compute_returns(_prices())
    assert r.shape == (99, 3)


def test_negative_price_rejected():
    p = _prices()
    p.iloc[5, 0] = -1
    with pytest.raises(ValueError):
        compute_returns(p)


def test_clean_returns_no_nan():
    r = clean_returns(compute_returns(_prices()))
    assert not r.isna().any().any()


def test_predictions_to_mu():
    df = pd.DataFrame({"date": ["2026-01-05"] * 2,
                       "symbol": ["A", "B"],
                       "ensemble_prediction": [0.01, 0.02]})
    mu = predictions_to_mu(df, "2026-01-05", horizon_days=5)
    assert np.isclose(mu["A"], 0.01 * 252 / 5)