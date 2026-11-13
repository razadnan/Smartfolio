"""
Conditional Value-at-Risk (CVaR / Expected Shortfall) Portfolio Optimization.
Formulation: Rockafellar & Uryasev (2000) convex linear programming.
"""

import numpy as np
import pandas as pd
import cvxpy as cp
from configs.config import W_MAX


def calculate_var_cvar(returns_matrix: np.ndarray, weights: np.ndarray, alpha: float = 0.95):
    """
    Compute empirical VaR and CVaR (Expected Shortfall) at confidence level alpha.
    Loss L = - Portfolio Return.
    VaR_alpha = Quantile_alpha(L)
    CVaR_alpha = E[ L | L >= VaR_alpha ]
    """
    port_returns = returns_matrix @ weights
    losses = -port_returns
    var = float(np.percentile(losses, alpha * 100))
    cvar_losses = losses[losses >= var]
    cvar = float(np.mean(cvar_losses)) if len(cvar_losses) > 0 else var
    return var, cvar


def min_cvar_portfolio(
    returns_df: pd.DataFrame,
    alpha: float = 0.95,
    w_max: float = W_MAX,
    target_return: float = None,
    mu: pd.Series = None,
    solver: str = "CLARABEL"
) -> pd.Series:
    """
    Solve for minimum CVaR portfolio weights using Rockafellar-Uryasev formulation.
    
    Parameters
    ----------
    returns_df : pd.DataFrame
        Historical return scenarios (T rows, N assets).
    alpha : float
        Confidence level for CVaR (default 0.95).
    w_max : float
        Maximum weight per asset.
    target_return : float, optional
        Minimum expected portfolio return constraint.
    mu : pd.Series, optional
        Expected return vector for target return constraint (default: sample mean).
    solver : str
        CVXPY solver to use.

    Returns
    -------
    pd.Series
        Asset weights summing to 1.0.
    """
    R = returns_df.values
    T, N = R.shape
    if T < 5:
        raise ValueError("Insufficient return history for CVaR optimization (T < 5).")

    symbols = returns_df.columns
    if mu is None:
        mu = returns_df.mean()
    else:
        mu = mu.reindex(symbols).fillna(0.0)

    # Decision variables
    w = cp.Variable(N)
    gamma = cp.Variable()  # VaR threshold
    u = cp.Variable(T)      # Slack variables for tail losses

    # Loss constraints: u_t >= -R_t * w - gamma, u_t >= 0
    # Matrix form: u + R @ w + gamma >= 0
    constraints = [
        u >= 0,
        u + R @ w + gamma >= 0,
        cp.sum(w) == 1.0,
        w >= 0.0,
        w <= w_max
    ]

    if target_return is not None:
        constraints.append(mu.values @ w >= target_return)

    # Objective: min gamma + 1/((1 - alpha) * T) * sum(u)
    cvar_term = gamma + (1.0 / ((1.0 - alpha) * T)) * cp.sum(u)
    objective = cp.Minimize(cvar_term)

    prob = cp.Problem(objective, constraints)
    try:
        prob.solve(solver=solver)
    except Exception:
        prob.solve(solver="HIGHS")

    if prob.status not in ["optimal", "optimal_inaccurate"] or w.value is None:
        # Fallback to equal weight if solver failed
        eq = 1.0 / N
        return pd.Series(np.full(N, eq), index=symbols)

    w_opt = np.array(w.value).flatten()
    w_opt = np.clip(w_opt, 0.0, w_max)
    w_opt = w_opt / np.sum(w_opt)

    return pd.Series(w_opt, index=symbols)
