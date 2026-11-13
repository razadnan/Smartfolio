import json
import platform
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from smartfolio.research.config import ROOT, load_config
from smartfolio.research.transaction_costs import cost_assumptions

RESULTS = ROOT / "results"
SYNTHETIC_SOURCES = {"mock", "synthetic"}


def _clean(o):
    """Make anything JSON-safe (NaN -> null, numpy -> python, Timestamp -> date)."""
    if isinstance(o, dict):
        return {str(k): _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    if isinstance(o, np.bool_):
        return bool(o)
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, (float, np.floating)):
        return None if (np.isnan(o) or np.isinf(o)) else float(o)
    if isinstance(o, pd.Timestamp):
        return str(o.date())
    return o


def write_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(_clean(obj), f, indent=2)


def assert_official(data_source, official):
    """Synthetic data must never enter an official experiment result."""
    if official and data_source in SYNTHETIC_SOURCES:
        raise ValueError(f"Refusing official run: data source '{data_source}' is synthetic")


def save_experiment(res, data_source, out=None):
    out = Path(out or RESULTS)
    folder = out / res["experiment"]
    folder.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame({"gross": res["gross"], "net": res["net"]})
    df["equity"] = (1 + df["net"]).cumprod()
    df["drawdown"] = df["equity"] / df["equity"].cummax() - 1
    df.index.name = "date"
    df.to_parquet(folder / "returns.parquet")

    w = res["weights"].copy()
    w.index.name = "decision_date"
    w.to_parquet(folder / "weights.parquet")
    res["costs"].rename("cost").to_frame().to_parquet(folder / "costs.parquet")

    write_json(folder / "summary.json", {
        "experiment": res["experiment"],
        "period": f"{df.index[0].date()}/{df.index[-1].date()}",
        "data_source": data_source,
        "synthetic": data_source in SYNTHETIC_SOURCES,
        "net": res["summary"],
        "gross": res["summary_gross"],
    })
    if "decisions" in res:
        write_json(folder / "decisions.json", res["decisions"])
    for key in ("prediction_feedback", "portfolio_feedback"):
        if key in res and len(res[key]):
            res[key].to_parquet(folder / f"{key}.parquet")
    return folder


def save_manifest(data_source, official, extra=None, out=None):
    out = Path(out or RESULTS)
    write_json(out / "manifest.json", {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "data_source": data_source,
        "synthetic": data_source in SYNTHETIC_SOURCES,
        "official": official,
        "seed": load_config()["seed"],
        "config": load_config(),
        "cost_assumptions": cost_assumptions(),
        "versions": {"python": platform.python_version(),
                     "numpy": np.__version__, "pandas": pd.__version__},
        **(extra or {}),
    })