from fastapi.testclient import TestClient
from smartfolio.api.main import app

client = TestClient(app)


def test_market_quote_endpoint():
    r = client.get("/api/market/quote?symbols=RELIANCE,TCS")
    assert r.status_code == 200
    quotes = r.json()
    assert len(quotes) == 2
    symbols = {q["symbol"] for q in quotes}
    assert "RELIANCE" in symbols and "TCS" in symbols
    assert all("price" in q and q["price"] > 0 for q in quotes)


def test_market_universe_endpoint():
    r = client.get("/api/market/universe")
    assert r.status_code == 200
    universe = r.json()
    assert len(universe) >= 15
    assert any(item["symbol"] == "RELIANCE" for item in universe)


def test_live_optimization_endpoint():
    payload = {
        "holdings": [
            {"symbol": "RELIANCE", "shares": 50, "buy_price": 1200.0},
            {"symbol": "TCS", "shares": 30, "buy_price": 2400.0},
            {"symbol": "HDFCBANK", "shares": 100, "buy_price": 680.0}
        ],
        "risk_profile": "Moderate",
        "strategy": "max_sharpe",
        "investment_mode": "rebalance",
        "fresh_capital": 50000.0,
        "max_stock_weight": 0.30,
        "max_sector_weight": 0.45,
        "target_cash": 0.05,
        "max_turnover": 0.50
    }
    r = client.post("/api/portfolio/optimize-live", json=payload)
    assert r.status_code == 200
    res = r.json()
    assert res["status"] == "success"
    assert "health" in res and "score" in str(res["health"])
    assert "trades" in res and len(res["trades"]) > 0
    assert "costs" in res and res["costs"]["total_cost"] >= 0
    assert "efficient_frontier" in res and len(res["efficient_frontier"]) > 0
    assert "metrics" in res and "expected_return" in res["metrics"]["optimized"]


def test_fresh_capital_optimization_strictly_buy():
    """Verify that a new investor with no prior holdings receives ONLY BUY orders (no SELL, no HOLD)."""
    payload = {
        "holdings": [],
        "risk_profile": "Moderate",
        "strategy": "hrp",
        "investment_mode": "fresh",
        "fresh_capital": 500000.0,
        "max_stock_weight": 0.25,
        "max_sector_weight": 0.40,
        "target_cash": 0.02,
        "max_turnover": 1.0
    }
    r = client.post("/api/portfolio/optimize-live", json=payload)
    assert r.status_code == 200
    res = r.json()
    assert res["status"] == "success"
    assert res["investment_mode"] == "fresh"
    assert res["health"]["before"] is None
    assert res["metrics"]["current"] is None
    assert len(res["trades"]) > 0
    
    # Assert every single trade is BUY with positive shares
    for trade in res["trades"]:
        assert trade["action"] == "BUY", f"Expected BUY but got {trade['action']} for {trade['symbol']}"
        assert trade["trade_shares"] > 0
        assert trade["current_shares"] == 0
        assert trade["trade_val"] > 0


def test_index_live_quotes():
    """Verify live quotes for market benchmark indices (^NSEI and ^INDIAVIX)."""
    r = client.get("/api/market/quote?symbols=^NSEI,^INDIAVIX")
    assert r.status_code == 200
    quotes = r.json()
    assert len(quotes) == 2
    syms = {q["symbol"] for q in quotes}
    assert "^NSEI" in syms or "NIFTY" in syms
    for q in quotes:
        assert q["price"] > 0
        assert q["source"] in ("live", "cached_estimate")


def test_locked_symbols_respected():
    """Verify that locked symbols cannot be sold or bought; they must remain on HOLD."""
    payload = {
        "holdings": [
            {"symbol": "RELIANCE", "shares": 50, "buy_price": 1200.0},
            {"symbol": "TCS", "shares": 30, "buy_price": 2400.0},
            {"symbol": "HDFCBANK", "shares": 100, "buy_price": 680.0}
        ],
        "risk_profile": "Moderate",
        "strategy": "max_sharpe",
        "investment_mode": "rebalance",
        "fresh_capital": 0.0,
        "max_stock_weight": 0.35,
        "max_sector_weight": 0.50,
        "target_cash": 0.02,
        "max_turnover": 0.50,
        "locked_symbols": ["RELIANCE"]
    }
    r = client.post("/api/portfolio/optimize-live", json=payload)
    assert r.status_code == 200
    res = r.json()
    rel_trade = next(t for t in res["trades"] if t["symbol"] == "RELIANCE")
    assert rel_trade["action"] == "HOLD"
    assert rel_trade["trade_shares"] == 0
    assert rel_trade["target_shares"] == 50


def test_candidate_symbols_fresh_mode():
    """Verify that caller-supplied candidate symbols are strictly utilized in Fresh Mode."""
    candidate_basket = ["TCS", "INFY", "WIPRO", "HCLTECH"]
    payload = {
        "holdings": [],
        "risk_profile": "Aggressive",
        "strategy": "hrp",
        "investment_mode": "fresh",
        "fresh_capital": 200000.0,
        "max_stock_weight": 0.40,
        "max_sector_weight": 1.0,
        "target_cash": 0.02,
        "max_turnover": 1.0,
        "candidate_symbols": candidate_basket
    }
    r = client.post("/api/portfolio/optimize-live", json=payload)
    assert r.status_code == 200
    res = r.json()
    trade_symbols = [t["symbol"] for t in res["trades"]]
    assert len(trade_symbols) > 0
    assert all(sym in candidate_basket for sym in trade_symbols)


def test_empty_portfolio_health_score_zero():
    """Unallocated portfolio must return a score of 0 rather than 50."""
    from smartfolio.api.services.tradebulls_optimizer import compute_health_score
    score_res = compute_health_score({}, {}, 0.0, 0.0)
    assert score_res["total_score"] == 0
    assert score_res["rating"] == "Unallocated"


def test_greedy_knapsack_cash_efficiency():
    """Verify that greedy integer allocation reduces residual uninvested cash to < 2.5%."""
    payload = {
        "holdings": [],
        "risk_profile": "Moderate",
        "strategy": "hrp",
        "investment_mode": "fresh",
        "fresh_capital": 300000.0,
        "max_stock_weight": 0.25,
        "max_sector_weight": 0.40,
        "target_cash": 0.01,
        "max_turnover": 1.0
    }
    r = client.post("/api/portfolio/optimize-live", json=payload)
    assert r.status_code == 200
    res = r.json()
    assert res["residual_cash"] < 300000.0 * 0.025, f"Residual cash too high: {res['residual_cash']}"

