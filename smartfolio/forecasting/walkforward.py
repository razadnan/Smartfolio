import numpy as np
import pandas as pd
from smartfolio.forecasting.leakage import assert_temporal_split


def make_folds(first_test_year=2016, last_year=2026, val_months=12):
    folds = []
    for y in range(first_test_year, last_year + 1):
        ts = pd.Timestamp(f"{y}-01-01")
        folds.append({
            "year": y,
            "val_start": ts - pd.DateOffset(months=val_months),
            "test_start": ts,
            "test_end": pd.Timestamp(f"{y + 1}-01-01"),
        })
    return folds


def split(df, f):
    fit = df[df["target_date"] < f["val_start"]]
    val = df[(df["date"] >= f["val_start"]) & (df["target_date"] < f["test_start"])]
    test = df[(df["date"] >= f["test_start"]) & (df["date"] < f["test_end"])]
    assert_temporal_split(fit, val)
    assert_temporal_split(val, test)
    return fit, val, test
