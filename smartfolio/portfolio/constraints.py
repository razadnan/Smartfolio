"""Portfolio constraints: build cvxpy constraints and validate final weights."""
import numpy as np
import pandas as pd
import cvxpy as cp
from configs.config import W_MAX


def check_feasible(n_assets: int, w_max: float = W_MAX) -> None:
    """With sum(w)=1 and w<=w_max, need n_assets * w_max >= 1."""
    if n_assets * w_max < 1 - 1e-9:
        raise ValueError(
            f"Infeasible: {n_assets} assets with w_max={w_max} cannot sum to 1 "
            f"(need at least {int(np.ceil(1 / w_max))} assets)."
        )


def build_constraints(w: cp.Variable, w_max: float = W_MAX,
                      sector_indices: dict = None,
                      max_sector_weight: float = None,
                      locked_indices: dict = None,
                      current_w: np.ndarray = None,
                      max_turnover: float = None) -> list:
    """Long-only, single-stock cap, fully invested, with optional sector caps, locked symbols, and turnover budget."""
    cons = [w >= 0, w <= w_max, cp.sum(w) == 1]
    if sector_indices and max_sector_weight is not None:
        for sec, idxs in sector_indices.items():
            if idxs:
                cons.append(cp.sum(w[idxs]) <= max_sector_weight)
    if locked_indices:
        for idx, val in locked_indices.items():
            cons.append(w[idx] == val)
    if current_w is not None and max_turnover is not None and max_turnover < 1.0:
        cons.append(cp.norm1(w - current_w) <= 2.0 * max_turnover)
    return cons


def validate_weights(weights: pd.Series, w_max: float = W_MAX,
                     tol: float = 1e-6) -> dict:
    """Return constraint status; raise if any hard constraint is violated."""
    w = weights.values.astype(float)
    if not np.isfinite(w).all():
        raise ValueError("Weights contain NaN/Inf.")
    if abs(w.sum() - 1) > tol:
        raise ValueError(f"Weights sum to {w.sum():.8f}, expected 1.")
    if (w < -tol).any():
        raise ValueError("Negative weight found (short selling not allowed).")
    if (w > w_max + tol).any():
        raise ValueError(f"Weight exceeds cap of {w_max}.")
    return {
        "sum_to_one": True,
        "non_negative": True,
        "within_cap": True,
        "max_weight": float(w.max()),
    }


def clean_weights(weights: pd.Series, w_max: float = W_MAX,
                  tol: float = 1e-6) -> pd.Series:
    """Zero out solver dust, clip to [0, w_max], renormalize."""
    w = weights.clip(lower=0, upper=w_max)
    w[w < tol] = 0.0
    w = w / w.sum()
    return w


def cap_hit_flags(weights: pd.Series, w_max: float = W_MAX,
                  tol: float = 1e-4) -> pd.Series:
    """True where a stock is sitting at the max allocation cap."""
    return weights >= (w_max - tol)