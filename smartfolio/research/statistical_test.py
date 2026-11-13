import numpy as np

from smartfolio.research.config import load_config
from smartfolio.research.metrics import sharpe


def _block_indices(n, block, n_samples, rng):
    """Circular block bootstrap indices, shape (n_samples, n)."""
    n_blocks = int(np.ceil(n / block))
    starts = rng.integers(0, n, size=(n_samples, n_blocks))
    idx = (starts[:, :, None] + np.arange(block)[None, None, :]) % n
    return idx.reshape(n_samples, -1)[:, :n]


def _sharpe_2d(x, rf, ppy):
    ex = x - rf / ppy
    sd = ex.std(axis=1, ddof=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(sd > 0, ex.mean(axis=1) / sd * np.sqrt(ppy), np.nan)


def bootstrap_sharpe_diff(r_a, r_b, n_samples=None, block_size=None,
                          confidence=None, seed=None):
    """Paired block-bootstrap CI for Sharpe(a) - Sharpe(b)."""
    cfg = load_config()
    bs = cfg["bootstrap"]
    n_samples = n_samples or bs["n_samples"]
    block_size = block_size or bs["block_size"]
    confidence = confidence or bs["confidence"]
    seed = cfg["seed"] if seed is None else seed

    a, b = np.asarray(r_a, float), np.asarray(r_b, float)
    if a.shape != b.shape:
        raise ValueError("Return series must have the same length")
    keep = ~(np.isnan(a) | np.isnan(b))
    a, b = a[keep], b[keep]
    if len(a) < 2 * block_size:
        raise ValueError("Too few observations for the chosen block size")

    rng = np.random.default_rng(seed)
    idx = _block_indices(len(a), block_size, n_samples, rng)
    rf, ppy = cfg["risk_free_rate"], cfg["periods_per_year"]
    diffs = _sharpe_2d(a[idx], rf, ppy) - _sharpe_2d(b[idx], rf, ppy)

    alpha = 1 - confidence
    lo, hi = np.nanpercentile(diffs, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return {
        "observed_diff": float(sharpe(a) - sharpe(b)),
        "ci_low": float(lo),
        "ci_high": float(hi),
        "confidence": confidence,
        "n_samples": int(n_samples),
        "block_size": int(block_size),
        "seed": int(seed),
        "n_obs": int(len(a)),
    }


def promotion_decision(challenger_r, champion_r, **kw):
    """PROMOTED only if the entire CI of Sharpe(challenger) - Sharpe(champion) > 0."""
    res = bootstrap_sharpe_diff(challenger_r, champion_r, **kw)
    promoted = res["ci_low"] > 0
    return {
        "metric": "sharpe_difference",
        "observed_diff": res["observed_diff"],
        "confidence_interval": [res["ci_low"], res["ci_high"]],
        "n_samples": res["n_samples"],
        "block_size": res["block_size"],
        "seed": res["seed"],
        "decision": "PROMOTED" if promoted else "REJECTED",
        "reason": ("CI entirely above zero" if promoted else
                   "No statistically significant portfolio-level improvement"),
    }