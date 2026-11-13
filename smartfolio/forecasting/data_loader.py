import pandas as pd
import yfinance as yf
from smartfolio.forecasting.config import load_config, ROOT

STARTER_SYMBOLS = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "HINDUNILVR", "ITC",
    "SBIN", "BHARTIARTL", "KOTAKBANK", "LT", "AXISBANK", "ASIANPAINT",
    "MARUTI", "SUNPHARMA", "TITAN", "ULTRACEMCO", "NESTLEIND", "WIPRO", "ONGC",
]


def _fetch(ticker, start, end):
    df = yf.Ticker(ticker).history(start=start, end=end, auto_adjust=True)
    if df.empty:
        return None
    df = df.reset_index()
    df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize(None).dt.normalize()
    df = df.rename(columns=str.lower)[["date", "open", "high", "low", "close", "volume"]]
    df["is_synthetic"] = False
    return df


def download_all(symbols=None):
    cfg = load_config()
    d = cfg["data"]
    raw = ROOT / cfg["paths"]["raw"]
    raw.mkdir(parents=True, exist_ok=True)

    frames, failed = [], []
    for s in symbols or STARTER_SYMBOLS:
        df = _fetch(f"{s}.NS", d["start_date"], d["end_date"])
        if df is None:
            failed.append(s)
            continue
        df.insert(1, "symbol", s)
        frames.append(df)
    pd.concat(frames, ignore_index=True).to_parquet(raw / "prices.parquet", index=False)

    for name, key in [("index", "index_symbol"), ("vix", "vix_symbol")]:
        df = _fetch(d[key], d["start_date"], d["end_date"])
        if df is None:
            failed.append(d[key])
        else:
            df.to_parquet(raw / f"{name}.parquet", index=False)

    print(f"Saved {len(frames)} stocks. Failed: {failed or 'none'}")


if __name__ == "__main__":
    download_all()