"""
Robust and Uncertainty-Aware Portfolio Optimization & Risk Budgeting.

Includes:
1. Uncertainty-Aware Alpha penalization: mu_adj = mu_hat - lambda_unc * sigma_hat
2. Equal Risk Contribution (Risk Parity) optimizer
3. Analytical Risk Contribution decomposition: RC_i = w_i * (Sigma w)_i / sigma_p
4. Worst-case Robust Mean-Variance Optimization
"""

import numpy as np
import pandas as pd
import cvxpy as cp
from scipy.optimize import minimize
from configs.config import W_MAX, RISK_FREE_RATE


def calculate_risk_contributions(weights: np.ndarray, cov: np.ndarray) -> dict:
    """
    Compute total volatility, marginal risk contributions, and percentage risk contributions.
    
    port_var = w.T @ Sigma @ w
    port_vol = sqrt(port_var)
    marginal_contrib = Sigma @ w
    risk_contrib_i = w_i * (Sigma @ w)_i / port_vol
    percent_contrib_i = risk_contrib_i / port_vol = (w_i * (Sigma @ w)_i) / port_var
    """
    w = np.array(weights).flatten()
    port_var = float(w @ cov @ w)
    port_vol = np.sqrt(max(port_var, 1e-12))
    marginal = cov @ w
    abs_rc = (w * marginal) / port_vol
    pct_rc = (w * marginal) / max(port_var, 1e-12)

    return {
        "portfolio_variance": port_var,
        "portfolio_volatility": port_vol,
        "marginal_risk_contributions": marginal,
        "absolute_risk_contributions": abs_rc,
        "percent_risk_contributions": pct_rc,
    }


def uncertainty_aware_mu(
    mu_hat: pd.Series,
    forecast_std: pd.Series = None,
    returns_df: pd.DataFrame = None,
    penalty_lambda: float = 1.0,
) -> pd.Series:
    """
    Penalize uncertain alpha forecasts.
    mu_adj = mu_hat - lambda * sigma_mu

    If forecast_std is not provided, estimate epistemic standard error from history:
    sigma_mu = std(returns) / sqrt(T)
    """
    mu_adj = mu_hat.copy()
    if forecast_std is not None:
        std_err = forecast_std.reindex(mu_hat.index).fillna(mu_hat.std() if len(mu_hat) > 1 else 0.01)
    elif returns_df is not None:
        T = len(returns_df)
        std_err = returns_df[mu_hat.index].std() / np.sqrt(max(T, 1))
    else:
        # Default fallback: 15% relative uncertainty
        std_err = mu_hat.abs() * 0.15

    mu_adj = mu_adj - penalty_lambda * std_err
    return mu_adj


def robust_mvo_portfolio(
    mu: pd.Series,
    cov: pd.DataFrame,
    uncertainty_scale: float = 0.5,
    risk_aversion: float = 3.0,
    w_max: float = W_MAX,
    rf: float = RISK_FREE_RATE
) -> pd.Series:
    """
    Solve robust mean-variance optimization under box/ellipsoidal parameter uncertainty:
    max_w (mu - kappa * sigma_mu)^T w - (gamma / 2) * w^T Sigma w
    s.t. sum(w) = 1, 0 <= w_i <= w_max
    """
    symbols = cov.columns
    mu = mu.reindex(symbols).fillna(0.0)
    N = len(symbols)

    # Uncertainty vector estimated from diagonal asset variances
    asset_vols = np.sqrt(np.diag(cov.values))
    mu_penalized = mu.values - uncertainty_scale * (asset_vols / np.sqrt(252))

    w = cp.Variable(N)
    Sigma = cov.values
    # Make sure Sigma is strictly positive semidefinite
    Sigma_psd = cp.psd_wrap(Sigma)

    ret_term = mu_penalized @ w
    risk_term = 0.5 * risk_aversion * cp.quad_form(w, Sigma_psd)
    objective = cp.Maximize(ret_term - risk_term)

    constraints = [
        cp.sum(w) == 1.0,
        w >= 0.0,
        w <= w_max
    ]

    prob = cp.Problem(objective, constraints)
    try:
        prob.solve(solver="CLARABEL")
    except Exception:
        prob.solve(solver="OSQP")

    if prob.status not in ["optimal", "optimal_inaccurate"] or w.value is None:
        eq = 1.0 / N
        return pd.Series(np.full(N, eq), index=symbols)

    w_opt = np.array(w.value).flatten()
    w_opt = np.clip(w_opt, 0.0, w_max)
    w_opt = w_opt / np.sum(w_opt)
    return pd.Series(w_opt, index=symbols)


def risk_parity_portfolio(cov: pd.DataFrame, w_max: float = W_MAX) -> pd.Series:
    """
    Solve for Equal Risk Contribution (Risk Parity) weights:
    min sum_i sum_j (RC_i - RC_j)^2
    s.t. sum(w) = 1, 0 <= w_i <= w_max
    """
    symbols = cov.columns
    N = len(symbols)
    Sigma = cov.values

    def objective(w):
        port_var = w @ Sigma @ w
        if port_var <= 1e-14:
            return 0.0
        # Target risk contribution is 1/N * port_var
        rc = w * (Sigma @ w)
        target = port_var / N
        return np.sum((rc - target) ** 2)

    w0 = np.full(N, 1.0 / N)
    bounds = [(0.001, w_max) for _ in range(N)]
    constraints = {"type": "eq", "fun": lambda w: np.sum(w) - 1.0}

    res = minimize(objective, w0, method="SLSQP", bounds=bounds, constraints=constraints)
    if res.success:
        w_opt = res.x / np.sum(res.x)
    else:
        # Fallback to inverse volatility
        vols = np.sqrt(np.diag(Sigma))
        inv_vols = 1.0 / np.maximum(vols, 1e-6)
        w_opt = inv_vols / np.sum(inv_vols)
        w_opt = np.clip(w_opt, 0.0, w_max)
        w_opt = w_opt / np.sum(w_opt)

    return pd.Series(w_opt, index=symbols)
