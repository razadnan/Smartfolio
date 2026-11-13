import numpy as np
import pytest

from smartfolio.research.statistical_test import bootstrap_sharpe_diff, promotion_decision


def _base():
    return np.random.default_rng(1).normal(0.0005, 0.01, 500)


def test_reproducible_with_seed():
    a, b = _base(), _base() * 0.9
    assert bootstrap_sharpe_diff(a, b) == bootstrap_sharpe_diff(a, b)


def test_clear_improvement_promoted():
    b = _base()
    res = promotion_decision(b + 0.002, b)
    assert res["decision"] == "PROMOTED"
    assert res["confidence_interval"][0] > 0


def test_identical_series_rejected():
    b = _base()
    res = promotion_decision(b.copy(), b)
    assert res["decision"] == "REJECTED"
    assert res["confidence_interval"][0] <= res["confidence_interval"][1]


def test_length_mismatch_raises():
    with pytest.raises(ValueError):
        bootstrap_sharpe_diff(np.zeros(100), np.zeros(90))