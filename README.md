# SmartFolio — Real-Time Institutional Portfolio Optimizer

**Enterprise-Grade Real-Time Portfolio Optimization, Risk Diagnostics, and Quantitative Asset Allocation Platform for Indian Equities (NSE / NIFTY 50)**

---

## 🌟 Key Features

- **Live NSE India Market Ingestion:** Real-time prices (CMP), percentage returns, and volume pulled via `yfinance` with 5-minute memory caching.
- **Tradebulls-Style Portfolio Health Scoring (0–100):** Real-time evaluation of position concentration (Herfindahl-Hirschman Index), sector diversification, beta exposure, and Sharpe efficiency.
- **Hierarchical Risk Parity (HRP) & CVXPY Optimization:** Marcos López de Prado's graph-theory clustering algorithm (tree clustering, quasi-diagonalization, recursive bisection) alongside Markowitz quadratic optimization under Ledoit-Wolf shrinkage.
- **Stock Market Terminal Experience:** Dual entry flow for fresh capital vs. rebalancing, interactive 52-week High/Low range bars, multi-column sorting, and sector filters.
- **3 Flexible Investment Modes:**
  1. *Rebalance Existing Portfolio:* Realigns drifted positions while respecting turnover caps.
  2. *Allocate Fresh Capital:* Invests lump-sum funds (e.g. ₹5,00,000) across optimal risk-adjusted weights from scratch.
  3. *Hybrid Top-Up:* Injects fresh capital while simultaneously rebalancing existing assets.
- **Demat-Ready Order Slip Generation:** Integer share calculation with statutory cost model (STT 0.1%, Brokerage, GST 18%, Stamp Duty, SEBI turnover fees).
- **1-Click Broker Basket Export:** Instant CSV export formatted for direct import into **Zerodha Kite**, **Groww**, and **Tradebulls Touch**.
- **Interactive Efficient Frontier Plot:** Real-time parametric risk-return curve visualizing your Current Portfolio vs. Optimal (Max Sharpe) allocation.
- **E0–E6 Research Ladder & Governance:** Walk-forward out-of-sample backtest validating machine learning alpha models with a Champion-Challenger retraining gate.

---

## Project Structure

```
smartfolio/
├── smartfolio/
│   ├── forecasting/    # Feature engineering, XGBoost, LSTM, Ensemble
│   ├── portfolio/      # Markowitz, Ledoit-Wolf shrinkage, constraints, turnover
│   ├── research/       # Backtesting engine, Champion-Challenger, E0-E6 experiments
│   └── api/            # Production FastAPI backend + Real-Time Market Data Services
├── tests/              # 121 unit & integration tests
├── frontend/           # Modern SPA Dashboard (HTML/CSS/JS with zero external CDNs)
├── configs/            # Unified configuration (YAML & Python constants)
├── examples/           # Sample inputs and handoff outputs
├── data/               # Market cache & raw datasets
├── results/            # Out-of-sample research results & promotion logs
├── pyproject.toml      # Packaging & dependencies
└── pytest.ini          # Test runner configuration
```

---

## 🚀 Quickstart & Setup

### 1. Environment & Installation
```bash
# Activate virtual environment
.\.venv\Scripts\activate      # Windows
source .venv/bin/activate     # Linux/macOS

# Install in editable mode with development dependencies
pip install -e .[dev]
```

### 2. Run All Tests (121 unit & integration tests)
```bash
pytest
```

### 3. Launch the Platform
```bash
uvicorn smartfolio.api.main:app --reload --port 8000
```
Then visit **`http://127.0.0.1:8000/`** to access the dashboard, or open **`frontend/index.html`** directly in any web browser.

---

## 📡 Core API Endpoints

- `GET /` — Serves the interactive institutional dashboard
- `GET /health` — Service health & research ladder status
- `GET /stocks` — Complete NIFTY 50 universe with sectors & market caps
- `GET /predictions` — Forward-looking alpha & return forecasts
- `GET /api/market/quote?symbols=RELIANCE,TCS` — Live CMP and daily statistics
- `GET /api/market/universe` — Catalog of all tracked Indian equities
- `POST /api/portfolio/optimize-live` — Full Tradebulls-style quadratic optimization
- `GET /model-comparison` — E0–E6 walk-forward benchmark metrics & bootstrap CI
- `GET /champion-challenger` — Model retraining governance decision log
- `GET /docs` — Interactive OpenAPI / Swagger documentation
