"""Ledoit-Wolf shrinkage covariance estimation."""
import numpy as np
import pandas as pd
from sklearn.covariance import LedoitWolf
from configs.config import TRADING_DAYS


def ledoit_wolf_cov(returns: pd.DataFrame, annualize: bool = True):
    """
    Returns (cov_df, shrinkage_coefficient).
    Input: daily returns (index=date, columns=symbol), no NaNs.
    """
    if returns.shape[0] < returns.shape[1]:
        # still valid for LW, but flag it: fewer observations than assets
        pass
    if returns.isna().any().any():
        raise ValueError("Returns contain NaN; clean them first.")

    lw = LedoitWolf().fit(returns.values)
    cov = lw.covariance_
    if annualize:
        cov = cov * TRADING_DAYS

    cov_df = pd.DataFrame(cov, index=returns.columns, columns=returns.columns)
    validate_cov(cov_df)
    return cov_df, float(lw.shrinkage_)


def sample_cov(returns: pd.DataFrame, annualize: bool = True) -> pd.DataFrame:
    """Raw sample covariance (used by E1 baseline, no shrinkage)."""
    cov = returns.cov()
    return cov * TRADING_DAYS if annualize else cov


def validate_cov(cov: pd.DataFrame, tol: float = 1e-8) -> None:
    """Check shape, symmetry, finiteness, and positive semi-definiteness."""
    if cov.shape[0] != cov.shape[1]:
        raise ValueError("Covariance matrix must be square.")
    if not np.isfinite(cov.values).all():
        raise ValueError("Covariance contains NaN/Inf.")
    if not np.allclose(cov.values, cov.values.T, atol=tol):
        raise ValueError("Covariance matrix is not symmetric.")
    if np.linalg.eigvalsh(cov.values).min() < -tol:
        raise ValueError("Covariance matrix is not positive semi-definite.")