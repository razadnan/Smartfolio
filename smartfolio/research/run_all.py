import argparse

import pandas as pd

from smartfolio.research.champion import run_e6
from smartfolio.research.config import set_seed
from smartfolio.research.experiment_logger import (RESULTS, assert_official, save_experiment,
                                   save_manifest, write_json)
from smartfolio.research.experiments import run_experiment
from smartfolio.research.mock_data import make_predictions, make_returns
from smartfolio.research.statistical_test import bootstrap_sharpe_diff
from smartfolio.research.stand_ins import train_momentum

USING_STAND_INS = False
EXPS = ["E0", "E1", "E2", "E3", "E4", "E5"]


def _sig(a, b):
    x = pd.concat([a, b], axis=1, join="inner").dropna()
    return bootstrap_sharpe_diff(x.iloc[:, 0].values, x.iloc[:, 1].values)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--returns", help="parquet: daily returns, DatetimeIndex x symbols")
    ap.add_argument("--preds", help="parquet: Student 1 predictions")
    ap.add_argument("--official", action="store_true")
    ap.add_argument("--days", type=int, default=900)
    a = ap.parse_args()
    set_seed()

    if a.returns:
        returns, preds, source = pd.read_parquet(a.returns), pd.read_parquet(a.preds), "student1"
    else:
        returns = make_returns(a.days)
        preds, source = make_predictions(returns), "mock"
    assert_official(source, a.official)

    kw = {} if a.returns else dict(train_window=252, rebalance_days=21)
    results = {}
    for n in EXPS:
        print("running", n, flush=True)
        results[n] = run_experiment(n, returns, preds, **kw)
    print("running E6", flush=True)
    results["E6"] = run_e6(returns, train_momentum, **kw)

    for res in results.values():
        save_experiment(res, source)
    rows = [{"experiment": n, **r["summary"], "sharpe_gross": r["summary_gross"]["sharpe"]}
            for n, r in results.items()]
    net = {n: r["net"] for n, r in results.items()}
    write_json(RESULTS / "comparison.json", {
        "data_source": source, "synthetic": source != "student1",
        "experiments": rows,
        "significance": {"E6_vs_E0": _sig(net["E6"], net["E0"]),
                         "E6_vs_E2": _sig(net["E6"], net["E2"])},
    })
    write_json(RESULTS / "model_promotions.json", results["E6"]["decisions"])
    save_manifest(source, a.official, {"walk_forward_override": kw})

    print(pd.DataFrame(rows).round(3).to_string(index=False))
    for d in results["E6"]["decisions"]:
        print(d["date"], d["decision"], d.get("reason", ""))


if __name__ == "__main__":
    main()
