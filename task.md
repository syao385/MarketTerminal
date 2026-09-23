# Task List - Aether Momentum Algorithmic Trading System

**Document Version:** 2.0.0  
**Status:** Approved / Production-Current  
**Last Review:** September 2026  

---

## Milestone Execution Checklist

- `[x]` **Milestone 1: Local Data Engine & Quantitative Calculations (COMPLETED)**
  - `[x]` Create `feature/algo-integration` git branch
  - `[x]` Initialize `algo-engine/` subfolder structure
  - `[x]` Create Python `requirements.txt` and configurations (`config/setups.yaml`)
  - `[x]` Build Alpaca credentials manager & API configuration endpoints (`/api/settings`)
  - `[x]` Implement premarket Time-Slice RVOL ($RVOL_{TS}$) calculations (`calculations/rvol.py`)
  - `[x]` Implement regular hours Time-Slice RVOL ($RVOL_{RM}$) and Volume Pacing ($Acc_{Vol}$) calculations
  - `[x]` Implement daily option GEX parser (Put/Call Walls and GEX Flip levels) (`calculations/gex.py`)
  - `[x]` Implement centralized in-memory caching proxy (`CANDLE_CACHE`) with 120s TTL (`/api/candles`)

- `[x]` **Milestone 2: Setup Registry, Scanners & Backtester Lab (COMPLETED)**
  - `[x]` Define Python `BaseSetup` class and registry loader
  - `[x]` Implement logic triggers for all 15 setups
  - `[x]` Implement the 3 tailored scorecards (MOS-B, MOS-A, MOS-P)
  - `[x]` Implement historical backtesting simulation engine (`calculations/backtester.py`)
  - `[x]` Implement multi-parameter sweep grid-search optimizer (`calculations/optimizer.py`)
  - `[x]` Implement high-speed 30-thread parallel scanner across 260+ tickers (`calculations/scanner.py`)
  - `[x]` Create standalone verification test suites (`validate_calculations.bat`, `validate_backtester.bat`)

- `[x]` **Milestone 3: Order Execution & SQLite Persistent Journaling (COMPLETED)**
  - `[x]` Connect execution layer & settings to Alpaca Paper Trading
  - `[x]` Implement dynamic position sizing based on MOS scoring (Kelly Criterion risk allocation)
  - `[x]` Enforce strictly integer share position sizing (`int()`), zero fractional shares
  - `[x]` Enforce capital ceiling caps ($\le 15\%$ portfolio) and minimum stop floors ($\ge \$0.50$)
  - `[x]` Implement 3-tier institutional signal resolution (confluence boost, neutralization, opposing auto-flatten)
  - `[x]` Implement setup-tagged trade journaling and SQLite database persistence (`trading_system.db`)
  - `[x]` Expose REST endpoints for trade logs: `POST /api/journal`, `GET /api/journal`, `POST /api/journal/update`

- `[x]` **Milestone 4: Cockpit Integration & Custom Canvas Charting (COMPLETED)**
  - `[x]` Reallocate backend server to Port 8080 to isolate from Port 8000 (GammaGexTrading)
  - `[x]` Build custom dual-pane HTML5 canvas candlestick charting engine (top: price, bottom: volume/CVD)
  - `[x]` Overlay SMA 20, 50, 200, Options GEX Call/Put walls, and Zero-Gamma Flip lines
  - `[x]` Render transparent unmitigated daily gaps and 3-candle Fair Value Gaps (FVG)
  - `[x]` Color-code volume bars by RVOL intensity and plot Cumulative Volume Delta (CVD) flow line
  - `[x]` Implement timeframe selector buttons (`1D`, `1H`, `5M`, `1M`) with dynamic recalculations
  - `[x]` Build Playbook Scanner Cockpit with tabs for all 15 setups, live trigger table, and MOS scorecards
  - `[x]` Restructure Setup Journal sidebar with Today's Triggers and paginated SQLite Saved Logs
  - `[x]` Integrate watchlist warning alert badges (`⚠️ Count (MOS)`) across all 4 watchlists
  - `[x]` Create master one-click launch scripts (`run_backend.bat`, `launch_all_terminals.bat`)
  - `[x]` Execute end-to-end dry run and mathematical validation checks