"""Main entry point: predictions + returns -> validated portfolio (output contract)."""
import numpy as np
import pandas as pd
from configs.config import (W_MAX, RISK_FREE_RATE, RISK_AVERSION,
                            OPTIMIZER_VERSION, LOOKBACK_DAYS, MIN_OBS,
                            PREDICTION_HORIZON_DAYS)
from smartfolio.portfolio.returns import clean_returns, historical_mean_returns, predictions_to_mu
from smartfolio.portfolio.ledoit_wolf import ledoit_wolf_cov, sample_cov
from smartfolio.portfolio.markowitz import min_volatility, risk_aware, max_sharpe
from smartfolio.portfolio.hrp import hrp_portfolio
from smartfolio.portfolio.black_litterman import black_litterman as bl_model
from smartfolio.portfolio.cvar import min_cvar_portfolio
from smartfolio.portfolio.robust import robust_mvo_portfolio, risk_parity_portfolio, calculate_risk_contributions
from smartfolio.portfolio.constraints import validate_weights, cap_hit_flags

STRATEGIES = {"max_sharpe", "min_volatility", "risk_aware", "hrp", "black_litterman", "cvar", "robust_mvo", "risk_parity"}


def _run_strategy(strategy, mu, cov, w_max, rf, risk_aversion, hist=None):
    if strategy == "max_sharpe":
        return max_sharpe(mu, cov, rf=rf, w_max=w_max)
    if strategy == "min_volatility":
        return min_volatility(mu, cov, w_max=w_max)
    if strategy == "hrp":
        return hrp_portfolio(cov)
    if strategy == "black_litterman":
        return max_sharpe(mu, cov, rf=rf, w_max=w_max)
    if strategy == "cvar":
        if hist is not None and len(hist) > 10:
            return min_cvar_portfolio(hist, alpha=0.95, w_max=w_max, mu=mu)
        return min_volatility(mu, cov, w_max=w_max)
    if strategy == "robust_mvo":
        return robust_mvo_portfolio(mu, cov, uncertainty_scale=0.5, risk_aversion=risk_aversion, w_max=w_max, rf=rf)
    if strategy == "risk_parity":
        return risk_parity_portfolio(cov, w_max=w_max)
    return risk_aware(mu, cov, risk_aversion=risk_aversion, w_max=w_max)


def optimize_portfolio(returns: pd.DataFrame, date, strategy: str = "max_sharpe",
                       pred_df: pd.DataFrame = None,
                       mu_source: str = "predictions",   # "predictions" | "historical"
                       cov_method: str = "ledoit_wolf",  # "ledoit_wolf" | "sample"
                       w_max: float = W_MAX, rf: float = RISK_FREE_RATE,
                       risk_aversion: float = RISK_AVERSION,
                       horizon_days: int = PREDICTION_HORIZON_DAYS,
                       lookback: int = LOOKBACK_DAYS) -> dict:
    """
    returns : daily returns (index=date, cols=symbol), all history available.
    date    : decision date; only returns up to and including it are used.
    mu_source/cov_method let Student 3 build E1/E2/E3-E5 with the same function.
    """
    if strategy not in STRATEGIES:
        raise ValueError(f"Unknown strategy '{strategy}'. Use one of {STRATEGIES}.")
    date = pd.to_datetime(date)

    # 1. history up to date (no future data)
    hist = returns.loc[:date].tail(lookback)
    hist = clean_returns(hist, min_obs=min(MIN_OBS, len(hist)))

    # 2. expected returns
    if mu_source == "predictions":
        if pred_df is None:
            raise ValueError("pred_df required when mu_source='predictions'.")
        mu = predictions_to_mu(pred_df, date, horizon_days)
    elif mu_source == "historical":
        mu = historical_mean_returns(hist)
    else:
        raise ValueError("mu_source must be 'predictions' or 'historical'.")

    if strategy == "black_litterman":
        # Re-compute mu using Black-Litterman model
        # Build partial cov from available history
        cov_for_bl, _ = ledoit_wolf_cov(hist) if cov_method == "ledoit_wolf" else (sample_cov(hist), None)
        mu = bl_model(cov_for_bl, hist.mean())
        strategy = "black_litterman"  # keep for dispatch

    # 3. align universe
    symbols = [s for s in mu.index if s in hist.columns]
    dropped = sorted(set(mu.index) - set(symbols))
    hist, mu = hist[symbols], mu.loc[symbols]

    # 4. covariance
    if cov_method == "ledoit_wolf":
        cov, shrink = ledoit_wolf_cov(hist)
    elif cov_method == "sample":
        cov, shrink = sample_cov(hist), None
    else:
        raise ValueError("cov_method must be 'ledoit_wolf' or 'sample'.")

    # 5. optimize + validate
    w = _run_strategy(strategy, mu, cov, w_max, rf, risk_aversion, hist=hist)
    status = validate_weights(w, w_max)

    # 6. portfolio metrics
    wv, C = w.values, cov.loc[w.index, w.index].values
    port_var = float(wv @ C @ wv)
    port_vol = float(np.sqrt(port_var))
    port_ret = float(wv @ mu.loc[w.index].values)
    marginal = C @ wv                        # (Σw)_i
    risk_contrib = wv * marginal / port_var  # sums to 1
    beta = marginal / port_var               # asset sensitivity to portfolio
    caps = cap_hit_flags(w, w_max)

    holdings = []
    for i, s in enumerate(w.index):
        if wv[i] <= 0:
            continue
        holdings.append({
            "symbol": s,
            "weight": round(float(wv[i]), 6),
            "predicted_return": float(mu[s]),
            "risk_contribution": round(float(risk_contrib[i]), 6),
            "diversification_benefit": bool(beta[i] < 1.0),
            "max_cap_hit": bool(caps[s]),
        })

    return {
        "date": str(date.date()),
        "strategy": strategy,
        "optimizer_version": OPTIMIZER_VERSION,
        "mu_source": mu_source,
        "cov_method": cov_method,
        "weights": holdings,
        "expected_return": port_ret,
        "volatility": port_vol,
        "sharpe": (port_ret - rf) / port_vol if port_vol > 0 else None,
        "shrinkage": shrink,
        "n_assets": len(symbols),
        "dropped_symbols": dropped,
        "constraint_status": status,
        "optimization_status": "optimal",
    }
