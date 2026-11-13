import numpy as np
import pandas as pd
import pytest

from smartfolio.research import metrics as m


def test_prediction_metrics():
    assert m.mae([0, 0], [3, 4]) == 3.5
    assert m.rmse([0, 0], [3, 4]) == pytest.approx(np.sqrt(12.5))
    assert m.r2([1, 2, 3], [1, 2, 3]) == 1.0
    assert m.directional_accuracy([1, -1, 1], [2, 1, 3]) == pytest.approx(2 / 3)


def test_annual_return_and_drawdown():
    assert m.annual_return([0.1, 0.1], ppy=2) == pytest.approx(0.21)
    assert m.max_drawdown([0.1, -0.5, 0.0]) == pytest.approx(-0.5)


def test_sharpe_zero_vol_is_nan():
    assert np.isnan(m.sharpe([0.01, 0.01, 0.01]))


def test_sharpe_sortino_positive_for_uptrend():
    r = [0.01, 0.02, -0.005, 0.015, 0.01]
    assert m.sharpe(r) > 0
    assert m.sortino(r) > 0


def test_turnover():
    w = pd.DataFrame({"A": [0.5, 0.2], "B": [0.5, 0.8]})
    ts = m.turnover_series(w)
    assert ts.iloc[0] == pytest.approx(0.5)   # initial build
    assert ts.iloc[1] == pytest.approx(0.3)   # 0.5*(0.3+0.3)
    assert m.avg_turnover(w) == pytest.approx(0.3)