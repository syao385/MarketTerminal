# Aether Market Terminal (v2.0.0)

[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](https://github.com/syao385/MarketTerminal)
[![Python](https://img.shields.io/badge/python-3.12-brightgreen.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-teal.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-Proprietary-red.svg)](#)

> **High-Density Algorithmic Trading Workstation, Custom Canvas Charting Engine, Options GEX Boundaries, and Quantitative Momentum Playbook Execution System.**

---

## 1. Executive Overview

The **Aether Market Terminal** is a high-performance algorithmic trading cockpit and quantitative analysis workstation engineered for active momentum traders, quantitative researchers, and portfolio managers. The terminal bridges qualitative market context (real-time news catalysts, AI-grounded sentiment analysis, systemic macro indicators) with quantitative market microstructure (options gamma boundaries, time-slice relative volume pacing, fair value gaps, and multi-factor opportunity scorecards).

Version 2.0.0 transforms MarketTerminal from a front-end visualization prototype into a complete, multi-process algorithmic execution platform featuring a 30-thread parallel scanner, an in-memory cached market data proxy, a custom dual-pane HTML5 canvas charting engine, an SQLite persistent trade journal, a historical backtesting simulation lab, and a 15-setup momentum trading playbook.

---

## 2. Multi-Service Architecture & Port Registry

The workstation operates as a coordinated multi-service ecosystem across three dedicated local ports, ensuring separation of concerns, zero UI render blocking, and complete isolation from external rate limits:

`mermaid
graph TB
    subgraph Client Layer
        UI["Web Frontend Cockpit (index.html)<br>Vanilla JS + Custom HTML5 Canvas Engine"]
    end

    subgraph Core Terminal Service (Port 8080)
        API["FastAPI Backend Engine (algo-engine/src/server.py)"]
        Cache["Central yfinance CANDLE_CACHE (120s Memory TTL)"]
        Scanner["30-Thread Parallel Scanner (calculations/scanner.py)"]
        Backtester["Backtest & Optimizer Lab (calculations/backtester.py)"]
        DB[("SQLite Database (algo-engine/data/trading_system.db)")]
    end

    subgraph News & Sentiment Proxy (Port 3000)
        NodeProxy["Node.js RSS & CORS Proxy (proxy-server.js)"]
    end

    subgraph Options Gamma Desk (Port 8000)
        GexDesk["GammaGexTrading Engine (Port 8000)"]
    end

    subgraph External Providers
        YF["Yahoo Finance API"]
        Gemini["Google Gemini 3.6 Flash (Search Grounded)"]
        RSS["Institutional Feeds (NAAIM / AAII)"]
        Alpaca["Alpaca Paper Trading API"]
    end

    UI -- "REST / JSON" --> API
    UI -- "XML RSS Requests" --> NodeProxy
    API -- "Fetch Price Candles" --> YF
    API -- "Batch Catalyst Prompt" --> Gemini
    API -- "Cross-Query GEX Levels" --> GexDesk
    API -- "Read / Write Trade Journal" --> DB
    API -- "Sync API Keys" --> Alpaca
    NodeProxy -- "CORS Bypass SSL Fetch" --> RSS
    API --> Cache
    API --> Scanner
    API --> Backtester
`

### Port & Service Directory

| Service | Port | Local URL | Primary Script | Core Responsibilities |
| :--- | :--- | :--- | :--- | :--- |
| **MarketTerminal Cockpit** | **8080** | http://127.0.0.1:8080 | un_backend.bat | Web UI (/), Central yfinance proxy (/api/candles), Indicators (/api/metrics), Universal Scanner (/api/scanner), SQLite Journal (/api/journal), Backtester (/api/backtest). |
| **GammaGexTrading Desk** | **8000** | http://127.0.0.1:8000 | ../GammaGexTrading/run.bat | Options chain GEX calculations, call wall, put wall, and zero-gamma flip boundary computation. |
| **Node RSS Proxy** | **3000** | http://127.0.0.1:3000 | start-proxy.bat | CORS bypass proxy for institutional sentiment RSS/XML feeds (NAAIM, AAII). |

---

## 3. Key Features in Version 2.0.0

### A. Custom HTML5 Dual-Pane Canvas Charting Engine
* **Direct 2D Context Rendering:** Replaces heavy third-party iframes with a lightweight, high-frame-rate HTML5 canvas.
* **Top Pane (72% Height):** Candlestick wicks and bodies, SMA 20 (Blue), SMA 50 (Orange), SMA 200 (Purple), Options Call Wall (Green), Put Wall (Red), and Zero-Gamma Flip level (Gold).
* **Support / Resistance Zones:** Transparent rectangles identifying unmitigated overnight gaps and 3-candle Fair Value Gaps (FVG).
* **Bottom Pane (23% Height):** Volume bars color-coded by transaction direction and Relative Volume (RVOL) intensity, overlaid with a bright Cyan **Cumulative Volume Delta (CVD)** flow line tracking aggressive institutional order flow.
* **Timeframe Selectors:** Instant dynamic recalculation across 1D, 1H, 5M, and 1M resolutions.

### B. High-Speed 30-Thread Parallel Scanner
* **Universe Coverage:** Scans 260+ high-liquidity tickers (S&P 100 leaders, Nasdaq 100 components, retail momentum leaders) across all 15 playbook setups simultaneously.
* **Sub-10 Second Execution:** Python concurrent.futures.ThreadPoolExecutor with 30 worker threads leverages the central memory cache to scan the entire universe in under 10 seconds.
* **Watchlist Alert Badges:** Displays real-time warning badges (⚠️ Count (MOS)) in all 4 watchlists (Personal, Portfolio, In-Play, Premarket Gappers).

### C. The 15 Institutional Momentum Playbook Setups
* **Category A: Breakout & Momentum Shock (MOS-B)**
  1. *Setup 1: Gap and Go (5m Intraday)*
  2. *Setup 3: Episodic Pivot / PEAD (1d / 5m)*
  3. *Setup 4: High-Tight Flag Breakout (1d / 5m)*
  4. *Setup 12: Standard Opening Range Breakout (ORB) (5m)*
  5. *Setup 13: Blue Sky / All-Time High Breakout (1d)*
  6. *Setup 15: PEAD Consolidation Breakout (1d)*
* **Category B: Volatility Contraction & Basing (MOS-A)**
  7. *Setup 9: Volatility Contraction Pattern (VCP) (1d)*
  8. *Setup 14: Stage 1 to Stage 2 Trend Reversal (200 SMA) (1d)*
* **Category C: Pullback & Mean-Reversion (MOS-P)**
  9. *Setup 2: Gap and Fade (5m Short)*
  10. *Setup 5: VWAP Hold & Re-Entry (5m)*
  11. *Setup 6: Parabolic Exhaustion Short (1d / 5m)*
  12. *Setup 7: Red-to-Green (R2G) Intraday Reversal (5m)*
  13. *Setup 8: Second Day Momentum Continuation (1d / 5m)*
  14. *Setup 10: 10/21 EMA Pullback (5m)*
  15. *Setup 11: 30-Minute Opening Range Breakout (15m)*

### D. SQLite Persistent Trade Journal & Execution Engine
* **Persistent Database:** lgo-engine/data/trading_system.db with journal_entries schema.
* **Strict Integer Position Sizing:** Floor sizing calculations (int()), zero fractional shares, capital ceiling caps ($\le 15\%$ portfolio), and minimum stop floors ($\ge \.50$).
* **Institutional Multi-Signal Resolution:** Combines confluent setups into single positions (+0.5 boost), neutralizes opposing signals ($|\Delta| < 1.5$), and auto-flattens opposing open trades on high-conviction signals ($\ge 8.5$).
* **Interactive UI Sidebar:** Today's Triggers panel, paginated Saved Logs with thumbnail charts, and status toggles (Win, Loss, Pending).

### E. Historical Backtester & Parameter Sweep Optimizer
* **Backtester Engine (acktester.py):** Historical simulation engine evaluating setup trigger conditions, scorecard-based Kelly sizing, partial profit targets (1.5R, 3.0R), breakeven stops, and adaptive trailing stops (10 EMA / 21 EMA / 50 SMA).
* **Grid-Search Optimizer (optimizer.py):** Automatically tests combinations of RVOL thresholds and risk-reward ratios to maximize net returns and profit factors.

### F. Central In-Memory Market Data Cache
* **Rate-Limit Immunity:** 120-second (2-minute) TTL memory cache in server.py.
* **Zero Outbound Waste:** Cache hits resolve in $<1\text{ms}$, reducing outbound Yahoo Finance calls by over 85% and eliminating HTTP 429 errors.

---

## 4. Repository Structure

`
MarketTerminal/
│
├── README.md                              # Master project documentation (v2.0.0)
├── index.html                             # Full frontend trading cockpit & custom canvas engine
├── proxy-server.js                        # Node.js RSS & CORS bypass proxy server
├── run_backend.bat                        # Master one-click launcher for MarketTerminal (Port 8080)
├── start-proxy.bat                        # Launcher for Node RSS proxy (Port 3000)
├── start_indicators_server.bat            # Standalone launcher for FastAPI backend
├── validate_calculations.bat              # Mathematical validation test suite
├── validate_backtester.bat                # Backtest & parameter sweep validation test suite
├── .gitignore                             # Git ignore rules for caches, temporary & virtualenv files
│
├── algo-engine/                           # Python Algorithmic Execution Engine
│   ├── requirements.txt                   # Python dependencies (fastapi, uvicorn, yfinance, etc.)
│   ├── verify_playbook_calculations.py    # Math unit test runner (RVOL, GEX, live SPY test)
│   ├── verify_milestone_2.py              # Backtester and optimizer test runner
│   │
│   ├── config/                            # Engine configurations
│   │   ├── alpaca_config.json             # Alpaca API keys and paper trading configuration
│   │   └── setups.yaml                    # Modular threshold parameters for all 15 setups
│   │
│   ├── data/                              # Persistent storage
│   │   └── trading_system.db              # SQLite database (journal entries, logs, status)
│   │
│   └── src/                               # Application source code
│       ├── server.py                      # FastAPI server (Port 8080), proxy cache, REST endpoints
│       └── calculations/                  # Quantitative calculation modules
│           ├── backtester.py              # PlaybookBacktester simulation engine
│           ├── optimizer.py               # SetupParameterOptimizer grid-search sweeps
│           ├── scanner.py                 # 30-thread parallel PlaybookScanner (260+ tickers)
│           ├── scorecards.py              # MOS-B, MOS-A, MOS-P scorecards & Kelly sizing
│           ├── rvol.py                    # Time-slice RVOL (RVOL_TS, RVOL_RM) & acceleration
│           ├── gex.py                     # Options Gamma boundaries (Call/Put Walls, GEX Flip)
│           └── indicators.py              # SMAs, unmitigated daily gaps, Fair Value Gaps (FVG)
│
├── docs/                                  # Living Architectural & Engineering Specifications
│   ├── DESIGN_SPEC.md                     # System architecture & detailed component design (v2.0.0)
│   ├── FUNCTIONAL_SPEC.md                 # Product vision, functional matrix & roadmap (v2.0.0)
│   └── LESSONS_LEARNED_AND_ENHANCEMENT_PLANS.md # Retrospective, risk matrix & enhancements (v2.0.0)
│
├── userguide.md                           # Comprehensive end-user operations & decision manual (v2.0.0)
├── momentum_algo_playbook.md              # Mathematical formulas, scorecards & setup rules (v2.0.0)
├── functional_test_plan.md                # 5-subsystem verification plan & setup test matrix (v2.0.0)
├── implementation_plan.md                 # Staged milestones & architecture evolution (v2.0.0)
├── walkthrough.md                         # Cumulative implementation changelog & audit report (v2.0.0)
├── genesis-DESIGN.md                      # UI tokens, typography & component design system
└── task.md                                # Milestones and tasks checklist (v2.0.0)
`

---

## 5. Quickstart & Installation

### Prerequisites
1. **Python 3.12+** installed and available in PATH.
2. **uv** (recommended fast Python package manager) or standard pip.
3. **Node.js 18+** for the RSS proxy server.

### Startup Sequence

#### Option A: Master Launch (Fastest)
1. Double-click **un_backend.bat** in the project root.
2. The script will:
   - Clear any stale processes on Port 8080.
   - Start the FastAPI engine using uv with all dependencies.
   - Connect to the SQLite database.
   - Launch your default browser to http://127.0.0.1:8080/.

#### Option B: Multi-Desk Launch (With Options GEX Desk & RSS Proxy)
1. Launch **GammaGexTrading**: run un.bat in ../GammaGexTrading/ (Port 8000).
2. Launch **Node RSS Proxy**: double-click start-proxy.bat (Port 3000).
3. Launch **MarketTerminal Engine**: double-click un_backend.bat (Port 8080).

---

## 6. Verification & Automated Testing

The repository includes standalone validation suites to verify mathematical calculations, historical backtesting, and live market connections:

`ash
# 1. Run mathematical verification (RVOL, Options GEX, live SPY chain analysis):
.\validate_calculations.bat

# 2. Run backtesting simulation and parameter sweep optimization:
.\validate_backtester.bat
`

Both tests should exit with code   and print ALL MATHEMATICAL TESTS PASSED and Milestone 2 Verification Passed successfully!.

---

## 7. Living Documentation Index

All project documentation files are maintained as **living cumulative documents** under strict version control:

| Document | Current Version | Primary Focus |
| :--- | :--- | :--- |
| [userguide.md](userguide.md) | **v2.0.0** | Comprehensive user manual, daily routine, flowchart, and widget operations. |
| [docs/DESIGN_SPEC.md](docs/DESIGN_SPEC.md) | **v2.0.0** | Low-level software architecture, data flows, coordinate math, and database schemas. |
| [docs/FUNCTIONAL_SPEC.md](docs/FUNCTIONAL_SPEC.md) | **v2.0.0** | Functional module requirements, product features, and long-term roadmap. |
| [docs/LESSONS_LEARNED_AND_ENHANCEMENT_PLANS.md](docs/LESSONS_LEARNED_AND_ENHANCEMENT_PLANS.md) | **v2.0.0** | Architectural retrospectives, known bottlenecks, and future enhancements. |
| [momentum_algo_playbook.md](momentum_algo_playbook.md) | **v2.0.0** | Mathematical formulations for all 15 setups, scorecards, and portfolio rules. |
| [functional_test_plan.md](functional_test_plan.md) | **v2.0.0** | Subsystem test criteria, setup verification matrix, and manual QA procedures. |
| [implementation_plan.md](implementation_plan.md) | **v2.0.0** | Staged delivery milestones, architectural rationale, and branching model. |
| [walkthrough.md](walkthrough.md) | **v2.0.0** | Chronological changelog, verification results, and implementation audit. |
| [genesis-DESIGN.md](genesis-DESIGN.md) | **v2.0.0** | Genesis Design System color tokens, typography, elevation, and component rules. |
| [task.md](task.md) | **v2.0.0** | Progress checklist across all development milestones. |

---

## 8. Version History & Changelog

### Version 2.0.0 (Current Release - September 2026)
* **Custom Canvas Charting Engine:** Complete implementation of dual-pane HTML5 canvas chart with SMA 20/50/200, Call/Put Walls, GEX Flip lines, unmitigated gaps, FVGs, and Cumulative Volume Delta (CVD).
* **Playbook Scanner Cockpit:** 30-worker thread parallel scanner evaluating 260+ tickers across 15 setups in under 10 seconds.
* **Persistent SQLite Trade Journal:** 	rading_system.db with journal_entries table, integer share sizing, trailing stop calculations, and REST API.
* **Backtester & Parameter Sweep Lab:** Historical simulation engine with multi-stage exits, breakeven stops, and grid-search optimizer.
* **Central Data Proxy & Caching:** In-memory CANDLE_CACHE with 120s TTL eliminating Yahoo Finance HTTP 429 errors.
* **Watchlist Alert Badges:** Real-time setup warning badges (⚠️ Count (MOS)) across all watchlists.
* **Alpaca Settings Integration:** Secure API credentials manager and UI modal.
* **Living Documentation Suite:** Comprehensive overhaul of all architectural, functional, and user-facing specifications.

### Version 1.0.0 (Initial Release - July 2026)
* Stable initial frontend build with TradingView widget integration.
* AI sentiment analysis and 3-sentence analyst powered by Google Gemini.
* Multi-feed news streams (WSJ, CNBC, Reddit, Google News).
* Macro sentiment dashboard (AAII retail sentiment, NAAIM institutional exposure).
* Initial paper trading terminal with local portfolio tracking.
