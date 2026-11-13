import pytest

from smartfolio.research.experiments import run_experiment
from smartfolio.research.mock_data import make_predictions, make_returns

R = make_returns(300)
P = make_predictions(R)
KW = dict(train_window=100, rebalance_days=21)


def test_e0_equal_weights():
    res = run_experiment("E0", R, **KW)
    assert res["weights"].round(6).eq(1 / 8).all().all()


@pytest.mark.parametrize("name", ["E1", "E2", "E3", "E4", "E5"])
def test_experiment_runs(name):
    res = run_experiment(name, R, P, **KW)
    assert len(res["net"]) == 200
    assert res["summary"]["turnover"] >= 0


def test_missing_prediction_raises():
    with pytest.raises(ValueError):
        run_experiment("E3", R, P[P["date"] != R.index[99]], **KW)


def test_predictions_required():
    with pytest.raises(ValueError):
        run_experiment("E5", R, None, **KW)

