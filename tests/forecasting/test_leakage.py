import numpy as np
import pandas as pd
import pytest
from smartfolio.forecasting.config import ROOT, load_config
from smartfolio.forecasting.features import _stock_features, _market_frame
from smartfolio.forecasting.leakage import features_are_causal, target_alignment_errors, assert_temporal_split

FEAT = ROOT / "data/features/features.parquet"


def _fake_prices(n=800, seed=42):
    rng = np.random.default_rng(seed)
    close = 100 * np.exp(np.cumsum(rng.normal(0, 0.01, n)))
    return pd.DataFrame({"close": close, "volume": rng.integers(10**5, 10**6, n).astype(float)})


def _leaky(g):
    f = _stock_features(g)
    f["leak"] = g["close"].shift(-1) / g["close"] - 1  # deliberately uses tomorrow
    return f


def test_stock_features_are_causal():
    df = _fake_prices()
    cols = list(_stock_features(df).columns)
    assert features_are_causal(_stock_features, df, cols) == []


def test_detector_catches_leak():
    assert features_are_causal(_leaky, _fake_prices(), ["leak"]) != []


def test_split_overlap_detected():
    d = pd.date_range("2020-01-01", periods=10)
    bad_train = pd.DataFrame({"date": d[:6], "target_date": d[3:9]})
    good_train = pd.DataFrame({"date": d[:4], "target_date": d[2:6]})
    test = pd.DataFrame({"date": d[6:]})
    with pytest.raises(AssertionError):
        assert_temporal_split(bad_train, test)
    assert_temporal_split(good_train, test)


@pytest.mark.skipif(not FEAT.exists(), reason="run src.features first")
def test_target_alignment_real_data():
    h = load_config()["model"]["horizon_days"]
    f = pd.read_parquet(FEAT)
    p = pd.read_parquet(ROOT / "data/processed/prices_clean.parquet")
    assert target_alignment_errors(p, f, h) == (0, 0)
    ok = f["target_date"].notna()
    assert (f.loc[ok, "target_date"] > f.loc[ok, "date"]).all()


@pytest.mark.skipif(not FEAT.exists(), reason="run src.features first")
def test_market_features_are_causal():
    idx = pd.read_parquet(ROOT / "data/raw/index.parquet")
    vix = pd.read_parquet(ROOT / "data/raw/vix.parquet")
    full = _market_frame(idx, vix).set_index("date")
    cut = idx["date"].iloc[2000]
    part = _market_frame(idx[idx["date"] <= cut], vix[vix["date"] <= cut]).set_index("date")
    assert np.allclose(full.loc[part.index].values, part.values, equal_nan=True)