import pandas as pd
import pytest

from smartfolio.research.backtester import walk_forward
from smartfolio.research.experiments import e0, run_experiment
from smartfolio.research.mock_data import make_predictions, make_returns

R = make_returns(300)
P = make_predictions(R)
KW = dict(train_window=100, rebalance_days=21)


@pytest.mark.parametrize("name", ["E0", "E2", "E5"])
def test_two_runs_identical(name):
    a = run_experiment(name, R, P, **KW)
    b = run_experiment(name, R, P, **KW)
    pd.testing.assert_series_equal(a["net"], b["net"])
    pd.testing.assert_frame_equal(a["weights"], b["weights"])
    assert a["summary"] == b["summary"]


def test_turnover_counts_drift_trades():
    assert run_experiment("E0", R, **KW)["summary"]["turnover"] > 0


def test_no_drift_no_turnover():
    same = pd.DataFrame(0.01, index=R.index, columns=R.columns)
    assert walk_forward(same, e0, 100, 21)["turnover"].iloc[1:].sum() == pytest.approx(0)