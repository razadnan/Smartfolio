"""Markowitz mean-variance strategies: max_sharpe, min_volatility, risk_aware."""
import numpy as np
import pandas as pd
import cvxpy as cp
from configs.config import W_MAX, RISK_FREE_RATE, RISK_AVERSION
from smartfolio.portfolio.constraints import check_feasible, build_constraints, clean_weights


def _prep(mu: pd.Series, cov: pd.DataFrame):
    """Align mu and cov on the same symbols and validate."""
    symbols = [s for s in mu.index if s in cov.index]
    if len(symbols) < 2:
        raise ValueError("Need at least 2 assets present in both mu and cov.")
    mu = mu.loc[symbols].astype(float)
    cov = cov.loc[symbols, symbols]
    if not np.isfinite(mu.values).all():
        raise ValueError("Expected returns contain NaN/Inf.")
    return mu, cov


def _solve(prob: cp.Problem) -> None:
    # Try CLARABEL, OSQP, SCS, and default
    for solver in (cp.CLARABEL, cp.OSQP, cp.SCS, None):
        try:
            if solver is not None:
                prob.solve(solver=solver)
            else:
                prob.solve()
            if prob.status in ("optimal", "optimal_inaccurate") and prob.value is not None:
                return
        except Exception:
            continue
    if prob.status not in ("optimal", "optimal_inaccurate"):
        raise RuntimeError(f"Optimization failed: status={prob.status}")


def min_volatility(mu, cov, w_max: float = W_MAX,
                   sector_indices: dict = None,
                   max_sector_weight: float = None,
                   locked_indices: dict = None,
                   current_w: np.ndarray = None,
                   max_turnover: float = None) -> pd.Series:
    mu, cov = _prep(mu, cov)
    n = len(mu)
    check_feasible(n, w_max)
    w = cp.Variable(n)
    risk = cp.quad_form(w, cp.psd_wrap(cov.values))
    cons = build_constraints(
        w, w_max=w_max, sector_indices=sector_indices,
        max_sector_weight=max_sector_weight, locked_indices=locked_indices,
        current_w=current_w, max_turnover=max_turnover
    )
    _solve(cp.Problem(cp.Minimize(risk), cons))
    return clean_weights(pd.Series(w.value, index=mu.index), w_max)


def risk_aware(mu, cov, risk_aversion: float = RISK_AVERSION,
               w_max: float = W_MAX,
               sector_indices: dict = None,
               max_sector_weight: float = None,
               locked_indices: dict = None,
               current_w: np.ndarray = None,
               max_turnover: float = None) -> pd.Series:
    mu, cov = _prep(mu, cov)
    n = len(mu)
    check_feasible(n, w_max)
    if risk_aversion <= 0:
        raise ValueError("risk_aversion must be > 0.")
    w = cp.Variable(n)
    utility = mu.values @ w - (risk_aversion / 2) * cp.quad_form(
        w, cp.psd_wrap(cov.values))
    cons = build_constraints(
        w, w_max=w_max, sector_indices=sector_indices,
        max_sector_weight=max_sector_weight, locked_indices=locked_indices,
        current_w=current_w, max_turnover=max_turnover
    )
    _solve(cp.Problem(cp.Maximize(utility), cons))
    return clean_weights(pd.Series(w.value, index=mu.index), w_max)


def max_sharpe(mu, cov, rf: float = RISK_FREE_RATE,
               w_max: float = W_MAX,
               sector_indices: dict = None,
               max_sector_weight: float = None,
               locked_indices: dict = None,
               current_w: np.ndarray = None,
               max_turnover: float = None) -> pd.Series:
    mu, cov = _prep(mu, cov)
    n = len(mu)
    check_feasible(n, w_max)
    excess = mu.values - rf
    if excess.max() <= 0:
        raise ValueError("No asset has expected return above the risk-free "
                         "rate; Max Sharpe is undefined.")
    y = cp.Variable(n)
    k = cp.Variable()
    cons = [y >= 0, y <= w_max * k, cp.sum(y) == k, excess @ y == 1, k >= 0]
    if sector_indices and max_sector_weight is not None:
        for sec, idxs in sector_indices.items():
            if idxs:
                cons.append(cp.sum(y[idxs]) <= max_sector_weight * k)
    if locked_indices:
        for idx, val in locked_indices.items():
            cons.append(y[idx] == val * k)
    if current_w is not None and max_turnover is not None and max_turnover < 1.0:
        cons.append(cp.norm1(y - k * current_w) <= 2.0 * max_turnover * k)
    risk = cp.quad_form(y, cp.psd_wrap(cov.values))
    _solve(cp.Problem(cp.Minimize(risk), cons))
    w = pd.Series(y.value / k.value, index=mu.index)
    return clean_weights(w, w_max)
