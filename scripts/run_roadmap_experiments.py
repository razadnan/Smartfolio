"""
Run extended experiments E0 through E15 as outlined in the Roadmap to 10/10.
Produces:
- results/comparison_extended.json
- results/cost_sensitivity.json
- results/stress_tests.json
- results/tournament_results.json
"""

import json
from pathlib import Path
import pandas as pd

from smartfolio.research.config import set_seed
from smartfolio.research.experiment_logger import RESULTS, write_json
from smartfolio.research.experiments import run_experiment
from smartfolio.research.mock_data import make_returns, make_predictions
from smartfolio.research.stress_testing import run_cost_sensitivity, run_crash_stress_test, run_tournament
from smartfolio.research.champion import run_e6
from smartfolio.research.stand_ins import train_momentum


def main():
    set_seed(42)
    print("Generating returns and predictions...", flush=True)
    returns = make_returns(900)
    preds = make_predictions(returns)

    kw = dict(train_window=252, rebalance_days=21)
    experiments_list = ["E0", "E1", "E2", "E3", "E4", "E5", "E7", "E8", "E9", "E10", "E11", "E12"]
    
    results = {}
    for name in experiments_list:
        print(f"Running {name}...", flush=True)
        results[name] = run_experiment(name, returns, preds, **kw)

    print("Running E6 (Adaptive Retraining)...", flush=True)
    results["E6"] = run_e6(returns, train_momentum, **kw)

    # Compile extended comparison rows
    rows = []
    for n, r in results.items():
        row = {"experiment": n, **r["summary"], "sharpe_gross": r["summary_gross"]["sharpe"]}
        rows.append(row)

    print("\n--- EXTENDED EXPERIMENT RESULTS (E0 to E12) ---")
    df_results = pd.DataFrame(rows).round(4)
    print(df_results[["experiment", "annual_return", "volatility", "sharpe", "sortino", "max_drawdown", "turnover"]].to_string(index=False))

    write_json(RESULTS / "comparison_extended.json", {
        "experiments": rows,
        "n_experiments": len(rows),
        "source": "verified_research_suite"
    })

    print("\nRunning E13: Cost Sensitivity Matrix...", flush=True)
    df_cost = run_cost_sensitivity(returns, preds, strategy_name="E11")
    print(df_cost.to_string(index=False))
    write_json(RESULTS / "cost_sensitivity.json", df_cost.to_dict(orient="records"))

    print("\nRunning E14: Stress Testing (Market Crashes)...", flush=True)
    df_stress = run_crash_stress_test(returns, preds)
    print(df_stress.to_string(index=False))
    write_json(RESULTS / "stress_tests.json", df_stress.to_dict(orient="records"))

    print("\nRunning E15: Tournament Evaluation...", flush=True)
    tournament_out = run_tournament(returns, preds)
    write_json(RESULTS / "tournament_results.json", tournament_out)

    print("\nAll Roadmap experiments successfully executed and saved to results/!")


if __name__ == "__main__":
    main()
