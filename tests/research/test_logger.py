import json

import numpy as np
import pandas as pd
import pytest

from smartfolio.research.experiment_logger import _clean, assert_official, save_experiment
from smartfolio.research.experiments import run_experiment
from smartfolio.research.mock_data import make_returns


def test_official_guard():
    with pytest.raises(ValueError):
        assert_official("mock", True)
    assert_official("mock", False)
    assert_official("student1", True)


def test_clean_nan_and_numpy():
    out = _clean({"a": np.nan, "b": np.float64(1.5), "c": np.int64(2)})
    assert out == {"a": None, "b": 1.5, "c": 2}
    json.dumps(out)


def test_save_experiment(tmp_path):
    res = run_experiment("E0", make_returns(300), train_window=100, rebalance_days=21)
    folder = save_experiment(res, "mock", tmp_path)
    s = json.loads((folder / "summary.json").read_text())
    assert s["experiment"] == "E0" and s["synthetic"] is True and "sharpe" in s["net"]
    df = pd.read_parquet(folder / "returns.parquet")
    assert {"gross", "net", "equity", "drawdown"} <= set(df.columns)
    assert len(df) == 200 and (df["drawdown"] <= 0).all()