import pandas as pd
import pytest

from smartfolio.research.backtester import walk_forward
from smartfolio.research.experiments import e0
from smartfolio.research.feedback import (FeedbackTracker, feedback_as_of, forward_returns,
                          portfolio_feedback, prediction_feedback)
from smartfolio.research.mock_data import make_predictions, make_returns

R = make_returns(300)
P = make_predictions(R)
PFB = prediction_feedback(P, R, "ensemble_prediction", 5)


def test_forward_returns():
    r = pd.DataFrame(0.01, index=pd.bdate_range("2021-01-01", periods=20), columns=["A", "B"])
    f = forward_returns(r, 5)
    assert f.iloc[0, 0] == pytest.approx(1.01 ** 5 - 1)
    assert f.iloc[-5:].isna().all().all()


def test_prediction_feedback_alignment():
    row = PFB.iloc[0]
    i = R.index.get_loc(row["date"])
    assert R.index.get_loc(row["known_by"]) - i == 5
    manual = (1 + R[row["symbol"]].iloc[i + 1:i + 6]).prod() - 1
    assert row["actual"] == pytest.approx(manual)
    assert row["error"] == pytest.approx(row["prediction"] - row["actual"])


def test_feedback_as_of_blocks_future_outcomes():
    fb = feedback_as_of(PFB, R.index[100])
    assert (fb["known_by"] <= R.index[100]).all()
    assert 0 < len(fb) < len(PFB)


def test_portfolio_feedback_covers_all_periods():
    res = walk_forward(R, e0, 100, 21)
    pf = portfolio_feedback(res["weights"], res["net"])
    assert len(pf) == len(res["weights"])
    total = (1 + pf["realized_return"]).prod() - 1
    assert total == pytest.approx((1 + res["net"]).prod() - 1)


def test_trigger_conditions():
    idx = R.index
    t = FeedbackTracker()                       # never retrained
    assert t.check(PFB, idx[150], idx)["retrain"] is True
    t.mark_retrained(idx[100])
    assert t.check(PFB, idx[150], idx)["retrain"] is True    # 50 days, 50 obs
    assert t.check(PFB, idx[149], idx)["retrain"] is False   # 49 obs
    assert t.check(PFB, idx[110], idx)["retrain"] is False   # 10 days


def test_trigger_reason_and_reset():
    idx = R.index
    t = FeedbackTracker(last_retrain=idx[100])
    assert "trading days" in t.check(PFB, idx[110], idx)["reason"]
    t.mark_retrained(idx[150])
    assert t.check(PFB, idx[160], idx)["retrain"] is False