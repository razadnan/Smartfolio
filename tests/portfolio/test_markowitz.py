import numpy as np
import pandas as pd
import pytest
from smartfolio.portfolio.markowitz import min_volatility, risk_aware, max_sharpe
from smartfolio.portfolio.constraints import validate_weights


def _inputs(k=8):
    rng = np.random.default_rng(42)
    syms = [f"S{i}" for i in range(k)]
    A = rng.normal(0, 0.1, (k, k))
    cov = pd.DataFrame(A @ A.T + np.eye(k) * 0.04, index=syms, columns=syms)
    mu = pd.Series(rng.uniform(0.05, 0.25, k), index=syms)
    return mu, cov


def _vol(w, cov):
    return float(np.sqrt(w.values @ cov.loc[w.index, w.index].values @ w.values))


@pytest.mark.parametrize("fn", [min_volatility, risk_aware, max_sharpe])
def test_constraints_hold(fn):
    mu, cov = _inputs()
    w = fn(mu, cov)
    assert validate_weights(w)["within_cap"]


def test_min_vol_lowest_risk():
    mu, cov = _inputs()
    assert _vol(min_volatility(mu, cov), cov) <= _vol(max_sharpe(mu, cov), cov) + 1e-6


def test_max_sharpe_beats_min_vol_on_sharpe():
    mu, cov = _inputs()
    def sharpe(w):
        return (w.values @ mu.loc[w.index].values - 0.06) / _vol(w, cov)
    assert sharpe(max_sharpe(mu, cov)) >= sharpe(min_volatility(mu, cov)) - 1e-6


def test_high_lambda_approaches_min_vol():
    mu, cov = _inputs()
    w1 = risk_aware(mu, cov, risk_aversion=1000)
    w2 = min_volatility(mu, cov)
    assert np.allclose(w1.values, w2.loc[w1.index].values, atol=0.05)


def test_infeasible_assets():
    mu, cov = _inputs(k=2)
    with pytest.raises(ValueError):
        min_volatility(mu, cov)


def test_max_sharpe_all_below_rf():
    mu, cov = _inputs()
    with pytest.raises(ValueError):
        max_sharpe(mu * 0 + 0.01, cov)
        