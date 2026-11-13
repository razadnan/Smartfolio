import json
import pandas as pd
from smartfolio.forecasting.config import load_config, ROOT

OHLC = ["open", "high", "low", "close"]


def validate(df):
    """Return a dict of data-quality counts. Does not modify df."""
    ret = df.sort_values(["symbol", "date"]).groupby("symbol")["close"].pct_change()
    return {
        "rows": len(df),
        "symbols": int(df["symbol"].nunique()),
        "duplicates": int(df.duplicated(["symbol", "date"]).sum()),
        "missing_ohlc": int(df[OHLC].isna().any(axis=1).sum()),
        "non_positive_prices": int((df[OHLC] <= 0).any(axis=1).sum()),
        "high_lt_low": int((df["high"] < df["low"]).sum()),
        "future_dates": int((df["date"] > pd.Timestamp.today()).sum()),
        "extreme_moves_over_40pct": int((ret.abs() > 0.4).sum()),
        "synthetic_rows": int(df["is_synthetic"].sum()),
    }


def clean(df):
    df = df.drop_duplicates(["symbol", "date"], keep="last")
    df = df[df["date"] <= pd.Timestamp.today()]
    df = df.dropna(subset=OHLC)
    df = df[(df[OHLC] > 0).all(axis=1)]
    df = df[df["high"] >= df["low"]]
    df["volume"] = df["volume"].fillna(0)
    return df.sort_values(["symbol", "date"]).reset_index(drop=True)


def assert_no_synthetic(df):
    """Call this before any official experiment."""
    n = int(df["is_synthetic"].sum())
    if n:
        raise ValueError(f"{n} synthetic rows found. Not allowed in official results.")


def run():
    cfg = load_config()
    raw = ROOT / cfg["paths"]["raw"] / "prices.parquet"
    out = ROOT / cfg["paths"]["processed"]
    meta = ROOT / cfg["paths"]["metadata"]
    out.mkdir(parents=True, exist_ok=True)
    meta.mkdir(parents=True, exist_ok=True)

    df = pd.read_parquet(raw)
    before = validate(df)
    df = clean(df)
    after = validate(df)
    assert_no_synthetic(df)

    df.to_parquet(out / "prices_clean.parquet", index=False)
    with open(meta / "data_quality_report.json", "w") as f:
        json.dump({"before": before, "after": after}, f, indent=2)

    print("BEFORE:", before)
    print("AFTER: ", after)
    print(df.groupby("symbol").size().sort_values().head(3).to_string())


if __name__ == "__main__":
    run()