import numpy as np
import pandas as pd
import pytest
from smartfolio.portfolio.constraints import (check_feasible, validate_weights,
                             clean_weights, cap_hit_flags)


def test_feasibility_pass():
    check_feasible(3, 0.40)          # 3 * 0.4 = 1.2 >= 1


def test_feasibility_fail():
    with pytest.raises(ValueError):
        check_feasible(2, 0.40)      # 0.8 < 1


def test_valid_weights():
    w = pd.Series([0.4, 0.3, 0.3], index=list("ABC"))
    assert validate_weights(w)["within_cap"]


def test_sum_violation():
    with pytest.raises(ValueError):
        validate_weights(pd.Series([0.4, 0.3, 0.2]))


def test_negative_violation():
    with pytest.raises(ValueError):
        validate_weights(pd.Series([0.5, 0.6, -0.1]))


def test_cap_violation():
    with pytest.raises(ValueError):
        validate_weights(pd.Series([0.5, 0.3, 0.2]))


def test_nan_violation():
    with pytest.raises(ValueError):
        validate_weights(pd.Series([0.5, np.nan, 0.5]))


def test_clean_weights_removes_dust():
    w = clean_weights(pd.Series([0.4, 0.3, 0.3 - 1e-9, 1e-9], index=list("ABCD")))
    assert w["D"] == 0.0
    assert abs(w.sum() - 1) < 1e-9


def test_cap_hit():
    f = cap_hit_flags(pd.Series([0.4, 0.35, 0.25], index=list("ABC")))
    assert f["A"] and not f["B"]
    