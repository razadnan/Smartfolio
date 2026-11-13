import pandas as pd
import pytest

from smartfolio.research.backtester import validate_weights, walk_forward
from smartfolio.research.metrics import portfolio_summary
from smartfolio.research.mock_data import make_returns

ZERO = {"version": "t", "brokerage": 0, "stt": 0, "stamp_duty_buy": 0,
        "exchange_txn": 0, "sebi": 0, "gst": 0}


def equal(history, date):
    return pd.Series(1 / history.shape[1], index=history.columns)


def test_no_lookahead():
    r, calls = make_returns(300), []

    def strat(h, d):
        calls.append((h.index[-1], d))
        return equal(h, d)

    res = walk_forward(r, strat, 100, 21)
    for (last, d), wd in zip(calls, res["weights"].index):
        assert last == d == wd
    assert calls[0][0] == r.index[99]
    assert res["net"].index[0] == r.index[100]   # first return earned AFTER decision
    assert len(res["net"]) == 200


def test_constant_returns_zero_cost():
    r = pd.DataFrame(0.01, index=pd.bdate_range("2021-01-01", periods=200),
                     columns=["A", "B", "C"])
    res = walk_forward(r, equal, 100, 21, costs=ZERO)
    assert res["gross"].tolist() == pytest.approx([0.01] * 100)
    assert res["net"].tolist() == pytest.approx([0.01] * 100)


def test_costs_hit_first_day_of_each_block_only():
    res = walk_forward(make_returns(300), equal, 100, 21)
    diff = (res["gross"] - res["net"]).abs() > 1e-12
    assert diff.sum() == len(res["weights"])
    assert res["net"].sum() < res["gross"].sum()


def test_validate_weights():
    for bad in ({"A": 0.5, "B": 0.4}, {"A": 1.2, "B": -0.2}, {"A": 0.5, "B": 0.5}):
        with pytest.raises(ValueError):
            validate_weights(bad)
    assert validate_weights({"A": 0.4, "B": 0.3, "C": 0.3}).sum() == pytest.approx(1)


def test_summary_runs():
    res = walk_forward(make_returns(400), equal, 100, 21)
    s = portfolio_summary(res["net"], res["weights"])
    assert set(s) >= {"sharpe", "max_drawdown", "turnover"}