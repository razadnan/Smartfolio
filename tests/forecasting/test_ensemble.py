import numpy as np
import pandas as pd
import pytest
from smartfolio.forecasting.config import ROOT
from smartfolio.forecasting.ensemble import inv_mse_weights, combine, REQUIRED

PRED = ROOT / "data/processed/prediction.parquet"


def test_weights_sum_to_one_and_favor_better_model():
    y = np.linspace(-0.05, 0.05, 100)
    v = pd.DataFrame({"target": y, "xgb_prediction": y + 0.01, "lstm_prediction": y + 0.04})
    wx, wl = inv_mse_weights(v)
    assert abs(wx + wl - 1) < 1e-9 and wx > wl


def test_missing_model_falls_back():
    x = pd.Series([0.02, np.nan, 0.01])
    l = pd.Series([0.04, 0.03, np.nan])
    assert np.allclose(combine(x, l, 0.5), [0.03, 0.03, 0.01])


@pytest.mark.skipif(not PRED.exists(), reason="run src.ensemble first")
def test_output_schema():
    p = pd.read_parquet(PRED)
    assert all(c in p.columns for c in REQUIRED)
    assert not p.duplicated(["date", "symbol"]).any()
    assert p["ensemble_prediction"].notna().all()
    assert np.isfinite(p[["xgb_prediction", "lstm_prediction", "ensemble_prediction"]].to_numpy()).all()