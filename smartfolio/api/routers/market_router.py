"""
market_router.py — FastAPI router for real-time market quotes, stock search, and Tradebulls-style optimization.
"""
from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel, Field

from smartfolio.api.services.market_data import (
    get_live_quote, get_multiple_quotes, get_nifty_universe
)
from smartfolio.api.services.nse_universe import search_stocks, SECTOR_COLORS, NSE_STOCKS, ALL_SECTORS
from smartfolio.api.services.tradebulls_optimizer import run_tradebulls_optimization

router = APIRouter(prefix="/api", tags=["market & live optimization"])


class HoldingItem(BaseModel):
    symbol: str
    shares: int = Field(..., ge=0)
    buy_price: Optional[float] = Field(None, ge=0.0)


class LiveOptimizeRequest(BaseModel):
    holdings: List[HoldingItem]
    risk_profile: str = "Moderate"
    strategy: str = "max_sharpe"
    investment_mode: str = "rebalance"
    fresh_capital: float = 0.0
    max_stock_weight: float = Field(0.25, ge=0.05, le=0.50)
    max_sector_weight: float = Field(0.40, ge=0.15, le=1.0)
    target_cash: float = Field(0.02, ge=0.0, le=0.20)
    max_turnover: float = Field(0.50, ge=0.05, le=1.0)
    excluded_symbols: Optional[List[str]] = None
    locked_symbols: Optional[List[str]] = None
    candidate_symbols: Optional[List[str]] = None
    views: Optional[List[dict]] = None


@router.get("/market/quote")
def get_quote(symbols: str = Query(..., description="Comma-separated stock symbols e.g. RELIANCE,TCS")):
    sym_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    if not sym_list:
        raise HTTPException(status_code=400, detail="No symbols provided")
    return get_multiple_quotes(sym_list)


@router.get("/market/universe")
def get_universe():
    return get_nifty_universe()


@router.get("/market/search")
def search_stocks_endpoint(
    q: str = Query("", description="Search query: symbol, company name, sector or industry"),
    sector: Optional[str] = Query(None, description="Filter by sector e.g. IT, Financials"),
    cap: Optional[str] = Query(None, description="Filter by cap: Large, Mid, Small"),
    index: Optional[str] = Query(None, description="Filter by index: NIFTY 50, NIFTY 100, NIFTY Midcap, NIFTY 500"),
    limit: int = Query(20, ge=1, le=100, description="Max results to return"),
):
    """
    Live stock search with optional filters. Used by frontend autocomplete dropdown.
    Searches across symbol, company name, sector, and industry.
    """
    results = search_stocks(q, sector=sector, cap=cap, index=index, limit=limit)
    return {"query": q, "count": len(results), "results": results}


@router.get("/market/sectors")
def get_sectors():
    """Returns all sectors with stock counts and brand colors for visualization."""
    counts = {}
    for meta in NSE_STOCKS.values():
        sec = meta["sector"]
        counts[sec] = counts.get(sec, 0) + 1
    sectors = [
        {
            "name": s,
            "count": counts.get(s, 0),
            "color": SECTOR_COLORS.get(s, "#6b7280"),
        }
        for s in sorted(counts.keys())
    ]
    return {
        "sectors": sectors,
        "total_stocks": len(NSE_STOCKS),
        "total_sectors": len(sectors),
    }


@router.post("/portfolio/optimize-live")
def optimize_live(req: LiveOptimizeRequest):
    try:
        holdings_dicts = [h.model_dump() for h in req.holdings]
        res = run_tradebulls_optimization(
            holdings=holdings_dicts,
            risk_profile=req.risk_profile,
            strategy=req.strategy,
            investment_mode=req.investment_mode,
            fresh_capital=req.fresh_capital,
            max_stock_weight=req.max_stock_weight,
            max_sector_weight=req.max_sector_weight,
            target_cash=req.target_cash,
            max_turnover=req.max_turnover,
            excluded_symbols=req.excluded_symbols,
            locked_symbols=req.locked_symbols,
            candidate_symbols=req.candidate_symbols,
            views=req.views,
        )
        return res
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(exc)}")
