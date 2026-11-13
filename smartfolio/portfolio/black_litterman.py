"""
black_litterman.py — Black-Litterman portfolio expected returns.

Implements the canonical Black-Litterman (1990) model:
  - CAPM market-implied equilibrium returns (pi = lambda * Sigma * w_mkt)
  - Bayesian update with investor views via P, Q, Omega
  - No-view fallback: blend equilibrium + historical (60/40)

Reference: He & Litterman (1999), "The Intuition Behind Black-Litterman"
"""
import numpy as np
import pandas as pd
from typing import Optional


def market_implied_returns(
    cov: pd.DataFrame,
    market_weights: Optional[pd.Series] = None,
    risk_aversion: float = 3.0,
    risk_free_rate: float = 0.06,
) -> pd.Series:
    """
    Compute CAPM-implied equilibrium excess returns.
    pi = lambda * Sigma * w_mkt
    
    Parameters
    ----------
    cov : pd.DataFrame  (annualised covariance matrix, shape n×n)
    market_weights : pd.Series  equal-weight if None
    risk_aversion : float  (lambda, typically 2.5–4.0 for equity)
    risk_free_rate : float  annual risk-free rate
    
    Returns
    -------
    pd.Series  annualised expected excess returns
    """
    n = len(cov)
    if market_weights is None:
        market_weights = pd.Series(np.full(n, 1.0 / n), index=cov.index)
    else:
        market_weights = market_weights.reindex(cov.index).fillna(0)
        total = market_weights.sum()
        if total > 0:
            market_weights = market_weights / total

    Sigma = cov.values  # annualised
    w = market_weights.values
    pi = risk_aversion * Sigma @ w
    return pd.Series(pi + risk_free_rate / 252, index=cov.index)


def black_litterman(
    cov: pd.DataFrame,
    historical_mu: pd.Series,
    views: Optional[dict] = None,
    tau: float = 0.05,
    risk_aversion: float = 3.0,
    risk_free_rate: float = 0.06,
    market_weights: Optional[pd.Series] = None,
) -> pd.Series:
    """
    Black-Litterman posterior expected returns.

    Parameters
    ----------
    cov : pd.DataFrame  (daily covariance matrix, shape n×n)
    historical_mu : pd.Series  daily historical mean returns (from hist.mean())
    views : dict or None
        {
          "P": np.ndarray (k×n, picks matrix),
          "Q": np.ndarray (k,  view returns, annualised),
          "Omega": np.ndarray (k×k, view uncertainty diagonal, optional)
        }
    tau : float  scalar uncertainty in equilibrium (0.01–0.10)
    risk_aversion : float  lambda
    risk_free_rate : float  annual risk-free rate
    market_weights : pd.Series or None  cap weights for equilibrium

    Returns
    -------
    pd.Series  daily posterior expected returns (annualised / 252)
    """
    # Annualise covariance and historical mu
    Sigma_ann = cov * 252
    hist_ann = historical_mu * 252

    # CAPM equilibrium returns (annualised)
    pi_ann = market_implied_returns(Sigma_ann, market_weights, risk_aversion, risk_free_rate)

    if views is None or not views:
        # No-view case: blend equilibrium (60%) + historical (40%)
        mu_bl_ann = 0.60 * pi_ann + 0.40 * hist_ann.reindex(pi_ann.index).fillna(pi_ann)
        return mu_bl_ann / 252  # return to daily

    # ── Full BL posterior with investor views ──────────────────────────────
    P = np.array(views["P"])  # shape (k, n)
    Q = np.array(views["Q"])  # shape (k,)  — annualised view returns

    k, n = P.shape
    Sigma = Sigma_ann.values  # (n, n)  annualised

    # Omega: view uncertainty. Default: proportional to P*Sigma*P'
    if "Omega" in views and views["Omega"] is not None:
        Omega = np.array(views["Omega"])
    else:
        # He-Litterman default: Omega = diag(tau * P * Sigma * P')
        PS = P @ Sigma @ P.T
        Omega = np.diag(np.diag(tau * PS))

    # Posterior: Black-Litterman formula
    # mu_BL = [(tau*Sigma)^{-1} + P'*Omega^{-1}*P]^{-1} * [(tau*Sigma)^{-1}*pi + P'*Omega^{-1}*Q]
    tauS = tau * Sigma
    try:
        tauS_inv = np.linalg.inv(tauS)
        Omega_inv = np.linalg.inv(Omega)
    except np.linalg.LinAlgError:
        # Fallback: pseudo-inverse
        tauS_inv = np.linalg.pinv(tauS)
        Omega_inv = np.linalg.pinv(Omega)

    A = tauS_inv + P.T @ Omega_inv @ P
    b = tauS_inv @ pi_ann.values + P.T @ Omega_inv @ Q

    try:
        mu_bl_ann = np.linalg.solve(A, b)
    except np.linalg.LinAlgError:
        mu_bl_ann = np.linalg.lstsq(A, b, rcond=None)[0]

    return pd.Series(mu_bl_ann / 252, index=cov.index)
