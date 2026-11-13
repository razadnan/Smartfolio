"""Generate sample inputs and handoff outputs for Student 3."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from smartfolio.portfolio.optimizer import optimize_portfolio  # noqa: E402

OUT = ROOT / "examples"
SEED = 42


def make_sample(k=10, n=400):
    rng = np.random.default_rng(SEED)
    idx = pd.date_range("2024-01-01", periods=n, freq="B")
    syms = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
            "ITC", "LT", "SBIN", "AXISBANK", "MARUTI"][:k]
    rets = pd.DataFrame(rng.normal(0.0005, 0.011, (n, k)), index=idx, columns=syms)
    preds = pd.DataFrame({
        "date": str(idx[-1].date()),
        "symbol": syms,
        "xgb_prediction": rng.uniform(0.002, 0.02, k),
        "lstm_prediction": rng.uniform(0.002, 0.02, k),
    })
    preds["ensemble_prediction"] = (preds.xgb_prediction + preds.lstm_prediction) / 2
    preds["model_version"] = "forecast-v1.0"
    return rets, preds, idx[-1]


def main():
    rets, preds, date = make_sample()
    # mock inputs (same schema Student 1 will deliver)
    preds.to_csv(OUT / "sample_predictions.csv", index=False)
    rets.to_csv(OUT / "sample_returns.csv")

    results, rows = {}, []
    for strat in ["max_sharpe", "min_volatility", "risk_aware"]:
        out = optimize_portfolio(rets, date, strat, pred_df=preds)
        results[strat] = out
        for h in out["weights"]:
            rows.append({
                "date": out["date"], "symbol": h["symbol"], "weight": h["weight"],
                "expected_return": h["predicted_return"],
                "risk": out["volatility"], "strategy": strat,
                "optimizer_version": out["optimizer_version"],
            })

    (OUT / "portfolio_output.json").write_text(json.dumps(results, indent=2))
    pd.DataFrame(rows).to_parquet(OUT / "portfolio_weights.parquet", index=False)
    print("Written: portfolio_output.json, portfolio_weights.parquet")
    for s, o in results.items():
        print(f"{s:15s} ret={o['expected_return']:.3f} vol={o['volatility']:.3f} "
              f"sharpe={o['sharpe']:.2f} n={len(o['weights'])}")


if __name__ == "__main__":
    main()