"""Tests for NSE universe search and market API endpoints."""
import pytest
from fastapi.testclient import TestClient
from smartfolio.api.main import app
from smartfolio.api.services.nse_universe import NSE_STOCKS, search_stocks

client = TestClient(app)


def test_nse_universe_size():
    """Universe must contain at least 150 stocks."""
    assert len(NSE_STOCKS) >= 150, f"Expected >=150 stocks, got {len(NSE_STOCKS)}"


def test_nse_universe_required_fields():
    """Every entry must have name, sector, industry, cap, index fields."""
    for sym, meta in NSE_STOCKS.items():
        assert "name" in meta, f"{sym} missing 'name'"
        assert "sector" in meta, f"{sym} missing 'sector'"
        assert "industry" in meta, f"{sym} missing 'industry'"
        assert "cap" in meta, f"{sym} missing 'cap'"
        assert meta["cap"] in ("Large", "Mid", "Small"), f"{sym} has invalid cap: {meta['cap']}"


def test_search_by_symbol():
    results = search_stocks("RELIANCE")
    syms = [r["symbol"] for r in results]
    assert "RELIANCE" in syms


def test_search_by_name():
    results = search_stocks("Infosys")
    syms = [r["symbol"] for r in results]
    assert "INFY" in syms


def test_search_by_sector():
    results = search_stocks("", sector="IT", limit=50)
    for r in results:
        assert r["sector"] == "IT"
    assert len(results) >= 3


def test_search_by_cap():
    results = search_stocks("", cap="Large", limit=50)
    for r in results:
        assert r["cap"] == "Large"
    assert len(results) >= 10


def test_search_limit():
    results = search_stocks("", limit=5)
    assert len(results) <= 5


def test_api_market_search_endpoint():
    resp = client.get("/api/market/search?q=TATA&limit=10")
    assert resp.status_code == 200
    data = resp.json()
    assert "results" in data
    assert isinstance(data["results"], list)
    assert data["count"] == len(data["results"])


def test_api_market_search_empty_query():
    """Empty query returns up to limit stocks."""
    resp = client.get("/api/market/search?q=&limit=20")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["results"]) > 0


def test_api_market_search_sector_filter():
    resp = client.get("/api/market/search?q=&sector=Healthcare&limit=30")
    assert resp.status_code == 200
    data = resp.json()
    for r in data["results"]:
        assert r["sector"] == "Healthcare"


def test_api_market_sectors_endpoint():
    resp = client.get("/api/market/sectors")
    assert resp.status_code == 200
    data = resp.json()
    assert "sectors" in data
    assert "total_stocks" in data
    assert data["total_stocks"] >= 150
    assert len(data["sectors"]) >= 10
    for s in data["sectors"]:
        assert "name" in s
        assert "count" in s
        assert "color" in s
