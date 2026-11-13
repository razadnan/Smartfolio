import numpy as np
import pandas as pd


def features_are_causal(feature_fn, df, cols, cuts=(300, 600), tol=1e-9):
    """Return [(cut, col)] where truncated-data features differ from full-data features."""
    full = feature_fn(df)
    bad = []
    for cut in cuts:
        part = feature_fn(df.iloc[:cut])
        for c in cols:
            if not np.allclose(full.loc[part.index, c], part[c], atol=tol, equal_nan=True):
                bad.append((cut, c))
    return bad


def target_alignment_errors(prices, feats, h):
    """Return (wrong_target_values, wrong_target_dates) versus a fresh recomputation."""
    p = prices.sort_values(["symbol", "date"]).copy()
    g = p.groupby("symbol")
    p["exp"] = g["close"].transform(lambda s: s.shift(-h) / s - 1)
    p["exp_date"] = g["date"].shift(-h)
    m = feats.merge(p[["symbol", "date", "exp", "exp_date"]], on=["symbol", "date"])
    bad_t = ~np.isclose(m["target"], m["exp"], equal_nan=True)
    same_d = (m["target_date"] == m["exp_date"]) | (m["target_date"].isna() & m["exp_date"].isna())
    return int(bad_t.sum()), int((~same_d).sum())


def assert_temporal_split(train, test):
    """Train targets must be fully realized before the first test date."""
    last_known = train["target_date"].max()
    first_test = test["date"].min()
    if last_known >= first_test:
        raise AssertionError(f"Leakage: train targets end {last_known}, test starts {first_test}")