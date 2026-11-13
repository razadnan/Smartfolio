import pandas as pd
import pytest

from smartfolio.research.transaction_costs import cost_series, rebalance_cost, cost_assumptions


def test_initial_buy_cost():
    # 0.001 + 0.00015 + 0.0000307 * 1.18
    assert rebalance_cost({}, {"A": 1.0}) == pytest.approx(0.001186226, rel=1e-6)


def test_full_swap_costs_buy_plus_sell():
    # buy 0.001186226 + sell 0.001036226
    assert rebalance_cost({"A": 1.0}, {"B": 1.0}) == pytest.approx(0.002222452, rel=1e-6)


def test_no_trade_no_cost():
    assert rebalance_cost({"A": 0.5, "B": 0.5}, {"A": 0.5, "B": 0.5}) == 0.0


def test_cost_series_shape():
    w = pd.DataFrame({"A": [1.0, 0.0], "B": [0.0, 1.0]})
    cs = cost_series(w)
    assert cs.iloc[0] == pytest.approx(0.001186226, rel=1e-6)
    assert cs.iloc[1] == pytest.approx(0.002222452, rel=1e-6)


def test_assumptions_recorded():
    assert cost_assumptions()["version"] == "2026-09-22"