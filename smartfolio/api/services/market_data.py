"""
market_data.py — Real-time and historical market data service for NSE India.
Fetches live quotes, historical returns, and index data via yfinance.
Supports full NSE universe (~189 major stocks + all indices).
"""
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import concurrent.futures
import json
import logging
import time

import numpy as np
import pandas as pd
import yfinance as yf

from smartfolio.api.services.nse_universe import NSE_STOCKS, SECTOR_COLORS

logger = logging.getLogger("smartfolio.market_data")

CACHE_DIR = Path(__file__).resolve().parents[3] / "data" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Build NIFTY_UNIVERSE from the full NSE registry
NIFTY_UNIVERSE: Dict[str, dict] = {
    sym: {"name": meta["name"], "sector": meta["sector"], "cap": meta["cap"]}
    for sym, meta in NSE_STOCKS.items()
}
# Add index symbols
NIFTY_UNIVERSE.update({
    "^NSEI":     {"name": "NIFTY 50",    "sector": "Index", "cap": "Benchmark"},
    "NIFTY":     {"name": "NIFTY 50",    "sector": "Index", "cap": "Benchmark"},
    "^INDIAVIX": {"name": "India VIX",   "sector": "Index", "cap": "Volatility"},
    "INDIAVIX":  {"name": "India VIX",   "sector": "Index", "cap": "Volatility"},
    "^NSEBANK":  {"name": "NIFTY Bank",  "sector": "Index", "cap": "Benchmark"},
    "BANKNIFTY": {"name": "NIFTY Bank",  "sector": "Index", "cap": "Benchmark"},
})

INDEX_MAP = {
    "NIFTY":     "^NSEI",
    "NIFTY50":   "^NSEI",
    "^NSEI":     "^NSEI",
    "INDIAVIX":  "^INDIAVIX",
    "VIX":       "^INDIAVIX",
    "^INDIAVIX": "^INDIAVIX",
    "BANKNIFTY": "^NSEBANK",
    "^NSEBANK":  "^NSEBANK",
}

_QUOTE_CACHE: Dict[str, Tuple[float, dict]] = {}
CACHE_TTL_SECONDS = 300  # 5-minute memory cache


def _clean_symbol(s: str) -> str:
    s = s.strip().upper()
    if s.endswith(".NS"):
        s = s[:-3]
    return s


def _ns_symbol(s: str) -> str:
    clean = _clean_symbol(s)
    if clean in INDEX_MAP:
        return INDEX_MAP[clean]
    if clean.startswith("^"):
        return clean
    return f"{clean}.NS"


def get_live_quote(symbol: str) -> dict:
    """Fetch live quote for a single symbol with memory caching."""
    sym = _clean_symbol(symbol)
    now = time.time()
    if sym in _QUOTE_CACHE:
        ts, data = _QUOTE_CACHE[sym]
        if now - ts < CACHE_TTL_SECONDS:
            return data

    ticker_sym = _ns_symbol(sym)
    meta = NIFTY_UNIVERSE.get(sym, {"name": f"{sym} Ltd.", "sector": "Diversified", "cap": "Mid/Large"})

    try:
        t = yf.Ticker(ticker_sym)
        # Fetch latest 2 days of daily history for accurate close & change
        h = t.history(period="5d", auto_adjust=True)
        if not h.empty and "Close" in h:
            h = h.dropna(subset=["Close"])
        if not h.empty:
            latest = h.iloc[-1]
            prev = h.iloc[-2] if len(h) >= 2 else latest
            raw_p = float(latest["Close"])
            if not np.isnan(raw_p) and raw_p > 0:
                price = round(raw_p, 2)
                raw_prev = float(prev["Close"])
                prev_close = round(raw_prev, 2) if (not np.isnan(raw_prev) and raw_prev > 0) else price
                chg = round(price - prev_close, 2)
                chg_pct = round((chg / prev_close) * 100, 2) if prev_close > 0 else 0.0
                vol_val = latest.get("Volume", 0)
                volume = int(vol_val) if (not pd.isna(vol_val) and not np.isnan(float(vol_val))) else 0
                hi = float(latest.get("High", price))
                lo = float(latest.get("Low", price))

                res = {
                    "symbol": sym,
                    "name": meta["name"],
                    "sector": meta["sector"],
                    "price": price,
                    "prev_close": prev_close,
                    "change": chg,
                    "change_pct": chg_pct,
                    "volume": volume,
                    "high": round(hi, 2) if not np.isnan(hi) else price,
                    "low": round(lo, 2) if not np.isnan(lo) else price,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "source": "live",
                }
                _QUOTE_CACHE[sym] = (now, res)
                return res
    except Exception as exc:
        logger.warning(f"Live fetch failed for {ticker_sym}: {exc}")

    # Fallback to last known realistic estimate if network fails
    fallback_prices = {
        "RELIANCE": 1209.0, "TCS": 2529.0, "HDFCBANK": 706.9, "INFY": 1520.0,
        "ICICIBANK": 1260.0, "ITC": 472.0, "BHARTIARTL": 1655.0, "SBIN": 820.0,
        "LT": 3610.0, "SUNPHARMA": 1720.0, "TITAN": 3340.0, "TATAMOTORS": 940.0,
        "KOTAKBANK": 1790.0, "MARUTI": 12200.0, "ASIANPAINT": 2980.0, "WIPRO": 485.0,
        "BAJFINANCE": 7100.0, "HCLTECH": 1820.0, "M&M": 2850.0, "TRENT": 7200.0,
        "ZOMATO": 265.0, "MRF": 132000.0, "DIXON": 14500.0, "HAL": 4450.0, "BEL": 290.0,
        "NTPC": 415.0, "ONGC": 295.0, "POWERGRID": 330.0, "COALINDIA": 490.0, "TATASTEEL": 155.0
    }
    p = fallback_prices.get(sym, 1000.0)
    res = {
        "symbol": sym,
        "name": meta["name"],
        "sector": meta["sector"],
        "price": p,
        "prev_close": p,
        "change": 0.0,
        "change_pct": 0.0,
        "volume": 100000,
        "high": p * 1.01,
        "low": p * 0.99,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source": "cached_estimate",
    }
    _QUOTE_CACHE[sym] = (now, res)
    return res


def get_multiple_quotes(symbols: List[str], max_workers: int = 10) -> List[dict]:
    """Fetch live quotes for multiple symbols in parallel using a thread pool."""
    if len(symbols) <= 3:
        return [get_live_quote(s) for s in symbols]
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(max_workers, len(symbols))) as executor:
        future_to_sym = {executor.submit(get_live_quote, s): s for s in symbols}
        for future in concurrent.futures.as_completed(future_to_sym):
            sym = future_to_sym[future]
            try:
                results[sym] = future.result()
            except Exception as exc:
                logger.warning(f"Quote fetch failed for {sym}: {exc}")
    # Return in original order
    return [results[s] for s in symbols if s in results]


def get_historical_returns(symbols: List[str], lookback_days: int = 252) -> pd.DataFrame:
    """
    Download historical daily returns for requested symbols.
    Returns a DataFrame with DatetimeIndex and columns=symbols.
    """
    clean_syms = [_clean_symbol(s) for s in symbols]
    ns_syms = [_ns_symbol(s) for s in clean_syms]

    cache_file = CACHE_DIR / "daily_history.parquet"
    cached_df = None
    if cache_file.exists():
        try:
            mtime = cache_file.stat().st_mtime
            if (time.time() - mtime) < 21600:  # 6-hour cache
                cached_df = pd.read_parquet(cache_file)
                valid_cached = [s for s in clean_syms if s in cached_df.columns]
                if len(valid_cached) == len(clean_syms):
                    rets = cached_df[clean_syms].pct_change().dropna()
                    if len(rets) >= 30:
                        rets.attrs["data_source"] = "local_cache"
                        return rets.tail(lookback_days)
        except Exception:
            cached_df = None

    try:
        # Download batch close prices
        data = yf.download(ns_syms, period="1y", auto_adjust=True, progress=False)
        if not data.empty:
            if "Close" in data:
                closes = data["Close"]
            else:
                closes = data
            
            # Map column names back to clean symbols
            col_map = {}
            for c in closes.columns:
                c_clean = str(c).replace(".NS", "")
                col_map[c] = c_clean
            closes = closes.rename(columns=col_map)
            
            # Merge with existing cache if present
            if cached_df is not None:
                closes = closes.combine_first(cached_df)
            try:
                closes.to_parquet(cache_file)
            except Exception:
                pass

            # Keep only requested symbols that downloaded successfully
            valid_cols = [s for s in clean_syms if s in closes.columns]
            if len(valid_cols) >= 2:
                rets = closes[valid_cols].pct_change().dropna()
                if len(rets) >= 30:
                    rets.attrs["data_source"] = "live_download"
                    return rets.tail(lookback_days)
    except Exception as exc:
        logger.warning(f"Historical download failed: {exc}")

    # Fallback to realistic synthetic correlated returns
    logger.warning("Falling back to synthetic correlated returns due to download failure.")
    n_days = lookback_days
    n_assets = len(clean_syms)
    rng = np.random.default_rng(42)
    dates = pd.bdate_range(end=datetime.today(), periods=n_days)
    
    # Generate correlated random walk with Indian market characteristics
    market = rng.normal(0.0005, 0.010, n_days)
    matrix = np.zeros((n_days, n_assets))
    for i, s in enumerate(clean_syms):
        meta = NIFTY_UNIVERSE.get(s, {})
        sec = meta.get("sector", "Other")
        sec_factor = hash(sec) % 100 / 10000.0
        idio = rng.normal(0.0001 + sec_factor, 0.012, n_days)
        matrix[:, i] = 0.65 * market + 0.35 * idio

    synth_df = pd.DataFrame(matrix, index=dates, columns=clean_syms)
    synth_df.attrs["data_source"] = "synthetic_fallback"
    return synth_df


def get_nifty_universe() -> List[dict]:
    """Return catalog of full NSE universe with sectors, industries, cap categories."""
    from smartfolio.api.services.nse_universe import NSE_STOCKS
    result = []
    for sym, meta in NSE_STOCKS.items():
        result.append({
            "symbol": sym,
            "name": meta["name"],
            "sector": meta["sector"],
            "industry": meta["industry"],
            "cap": meta["cap"],
            "index": meta.get("index", "NSE"),
        })
    return result
