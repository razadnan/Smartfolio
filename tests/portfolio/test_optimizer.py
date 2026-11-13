import numpy as np
import pandas as pd
import pytest
from smartfolio.portfolio.optimizer import optimize_portfolio


def _data(k=10, n=300):
    rng = np.random.default_rng(42)
    idx = pd.date_range("2024-01-01", periods=n, freq="B")
    syms = [f"S{i}" for i in range(k)]
    rets = pd.DataFrame(rng.normal(0.0005, 0.01, (n, k)), index=idx, columns=syms)
    preds = pd.DataFrame({"date": str(idx[-1].date()), "symbol": syms,
                          "ensemble_prediction": rng.uniform(0.002, 0.02, k)})
    return rets, preds, idx[-1]


@pytest.mark.parametrize("strategy", ["max_sharpe", "min_volatility", "risk_aware"])
def test_output_contract(strategy):
    rets, preds, d = _data()
    out = optimize_portfolio(rets, d, strategy, pred_df=preds)
    ws = [h["weight"] for h in out["weights"]]
    assert abs(sum(ws) - 1) < 1e-4
    assert max(ws) <= 0.40 + 1e-6
    assert out["constraint_status"]["within_cap"]
    assert abs(sum(h["risk_contribution"] for h in out["weights"]) - 1) < 1e-3


def test_baselines_e1_e2():
    rets, _, d = _data()
    e1 = optimize_portfolio(rets, d, "max_sharpe", mu_source="historical",
                            cov_method="sample", rf=0.0)
    e2 = optimize_portfolio(rets, d, "max_sharpe", mu_source="historical",
                            cov_method="ledoit_wolf", rf=0.0)
    assert e1["shrinkage"] is None and e2["shrinkage"] is not None


def test_no_future_data():
    rets, preds, d = _data()
    early = rets.index[150]
    preds["date"] = str(early.date())
    out = optimize_portfolio(rets, early, "min_volatility", pred_df=preds)
    assert out["date"] == str(early.date())


def test_reproducible():
    rets, preds, d = _data()
    a = optimize_portfolio(rets, d, "max_sharpe", pred_df=preds)
    b = optimize_portfolio(rets, d, "max_sharpe", pred_df=preds)
    assert a["weights"] == b["weights"]


def test_bad_strategy():
    rets, preds, d = _data()
    with pytest.raises(ValueError):
        optimize_portfolio(rets, d, "nonsense", pred_df=preds)