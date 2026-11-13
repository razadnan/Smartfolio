"""
Unit tests for CVaR and Robust / Uncertainty-Aware Portfolio Optimization.
"""

import numpy as np
import pandas as pd
import pytest

from smartfolio.portfolio.cvar import min_cvar_portfolio, calculate_var_cvar
from smartfolio.portfolio.robust import (
    calculate_risk_contributions,
    uncertainty_aware_mu,
    robust_mvo_portfolio,
    risk_parity_portfolio
)
from smartfolio.portfolio.optimizer import optimize_portfolio


@pytest.fixture
def sample_returns():
    np.random.seed(42)
    symbols = ["RELIANCE", "TCS", "HDFCBANK", "INFY"]
    returns_arr = np.random.normal(0.0005, 0.015, size=(200, 4))
    dates = pd.date_range("2023-01-01", periods=200, freq="B")
    return pd.DataFrame(returns_arr, index=dates, columns=symbols)


def test_calculate_var_cvar(sample_returns):
    w = np.array([0.25, 0.25, 0.25, 0.25])
    var, cvar = calculate_var_cvar(sample_returns.values, w, alpha=0.95)
    assert var > 0
    assert cvar >= var  # CVaR (Expected Shortfall) is always >= VaR


def test_min_cvar_portfolio(sample_returns):
    w = min_cvar_portfolio(sample_returns, alpha=0.95, w_max=0.40)
    assert isinstance(w, pd.Series)
    assert len(w) == 4
    assert pytest.approx(w.sum(), 1e-4) == 1.0
    assert (w >= -1e-5).all()
    assert (w <= 0.40 + 1e-4).all()


def test_risk_contributions(sample_returns):
    cov = sample_returns.cov().values
    w = np.array([0.25, 0.25, 0.25, 0.25])
    rc = calculate_risk_contributions(w, cov)
    assert "percent_risk_contributions" in rc
    assert pytest.approx(rc["percent_risk_contributions"].sum(), 1e-4) == 1.0


def test_uncertainty_aware_mu(sample_returns):
    mu_hat = sample_returns.mean()
    mu_adj = uncertainty_aware_mu(mu_hat, returns_df=sample_returns, penalty_lambda=1.5)
    # Penalized mu should be strictly less than mu_hat for positive uncertainty
    assert (mu_adj <= mu_hat).all()


def test_robust_mvo(sample_returns):
    cov = sample_returns.cov()
    mu = sample_returns.mean()
    w = robust_mvo_portfolio(mu, cov, uncertainty_scale=0.5, risk_aversion=3.0, w_max=0.40)
    assert pytest.approx(w.sum(), 1e-4) == 1.0
    assert (w >= -1e-5).all()
    assert (w <= 0.40 + 1e-4).all()


def test_risk_parity_portfolio(sample_returns):
    cov = sample_returns.cov()
    w = risk_parity_portfolio(cov, w_max=0.40)
    assert pytest.approx(w.sum(), 1e-4) == 1.0
    assert (w >= -1e-5).all()


def test_optimizer_extended_strategies(sample_returns):
    date = sample_returns.index[-1]
    res_cvar = optimize_portfolio(sample_returns, date, strategy="cvar", mu_source="historical")
    assert res_cvar["constraint_status"]["sum_to_one"] is True
    assert len(res_cvar["weights"]) > 0

    res_robust = optimize_portfolio(sample_returns, date, strategy="robust_mvo", mu_source="historical")
    assert res_robust["constraint_status"]["sum_to_one"] is True

    res_parity = optimize_portfolio(sample_returns, date, strategy="risk_parity", mu_source="historical")
    assert res_parity["constraint_status"]["sum_to_one"] is True
