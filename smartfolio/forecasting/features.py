import numpy as np
import pandas as pd
from smartfolio.forecasting.config import load_config, ROOT

FEATURE_COLS = [
    "ret_1", "roc_5", "roc_10", "roc_20",
    "sma10_gap", "sma20_gap", "sma50_gap", "ema12_gap", "ema26_gap",
    "rsi_14", "macd", "macd_signal", "macd_hist",
    "vol_10", "vol_20", "volume_ratio",
    "mkt_ret_5", "mkt_vol_20", "vix", "vix_chg_5",
]


def _stock_features(g):
    c, v = g["close"], g["volume"]
    r = c.pct_change()
    out = pd.DataFrame(index=g.index)
    out["ret_1"] = r
    for n in (5, 10, 20):
        out[f"roc_{n}"] = c.pct_change(n)
    for n in (10, 20, 50):
        out[f"sma{n}_gap"] = c / c.rolling(n).mean() - 1
    ema12 = c.ewm(span=12, adjust=False, min_periods=12).mean()
    ema26 = c.ewm(span=26, adjust=False, min_periods=26).mean()
    out["ema12_gap"] = c / ema12 - 1
    out["ema26_gap"] = c / ema26 - 1

    d = c.diff()
    ag = d.clip(lower=0).ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    al = (-d.clip(upper=0)).ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    out["rsi_14"] = 100 - 100 / (1 + ag / al)

    macd = (ema12 - ema26) / c
    sig = macd.ewm(span=9, adjust=False, min_periods=9).mean()
    out["macd"], out["macd_signal"], out["macd_hist"] = macd, sig, macd - sig

    out["vol_10"] = r.rolling(10).std()
    out["vol_20"] = r.rolling(20).std()
    out["volume_ratio"] = v / v.rolling(20).mean().replace(0, np.nan)
    return out


def _market_frame(index, vix):
    m = index[["date", "close"]].sort_values("date").reset_index(drop=True)
    m["mkt_ret_5"] = m["close"].pct_change(5)
    m["mkt_vol_20"] = m["close"].pct_change().rolling(20).std()
    v = vix[["date", "close"]].rename(columns={"close": "vix"}).sort_values("date")
    v["vix_chg_5"] = v["vix"].pct_change(5)
    mk = m[["date", "mkt_ret_5", "mkt_vol_20"]].merge(v, on="date", how="outer")
    mk = mk.sort_values("date").ffill()  # forward-fill = past values only
    mk["date"] = mk["date"].astype("datetime64[ns]")
    return mk


def build_features():
    cfg = load_config()
    h = cfg["model"]["horizon_days"]
    proc, raw = ROOT / cfg["paths"]["processed"], ROOT / cfg["paths"]["raw"]
    prices = pd.read_parquet(proc / "prices_clean.parquet")
    idx = pd.read_parquet(raw / "index.parquet")
    vix = pd.read_parquet(raw / "vix.parquet")

    parts = []
    for sym, g in prices.groupby("symbol"):
        g = g.sort_values("date").reset_index(drop=True)
        f = _stock_features(g)
        f.insert(0, "symbol", sym)
        f.insert(0, "date", g["date"])
        f["target"] = g["close"].shift(-h) / g["close"] - 1
        f["target_date"] = g["date"].shift(-h)
        parts.append(f)

    df = pd.concat(parts, ignore_index=True)
    df["date"] = df["date"].astype("datetime64[ns]")
    df = pd.merge_asof(df.sort_values("date"), _market_frame(idx, vix),
                       on="date", direction="backward")
    df = df.replace([np.inf, -np.inf], np.nan).dropna(subset=FEATURE_COLS)
    df["feature_version"] = cfg["model"]["feature_version"]
    df = df.sort_values(["symbol", "date"]).reset_index(drop=True)

    out = ROOT / cfg["paths"]["features"]
    out.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out / "features.parquet", index=False)
    print(df.shape, "| rows with no target yet:", int(df["target"].isna().sum()))


if __name__ == "__main__":
    build_features()