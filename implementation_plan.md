# Implementation Plan - Aether Momentum Algorithmic Trading System (Phase 3)

This plan describes the architectural strategy and staged milestones to implement the 15-setup momentum trading playbook as a semi-automated/fully-automated algorithmic execution engine.

---

## 1. Project Organization: Versioning & Branching Strategy

To keep the existing production visual terminal ([index.html](file:///c:/Users/jfan/Documents/MarketTerminal/index.html)) fully functional and stable for daily trading, we recommend a **hybrid repository structure** in a **new Git branch**:

### A. Git Branching Model
*   **Branch Name:** `feature/algo-integration`
*   **Methodology:** All development for the algorithmic engine occurs in this branch. Once fully tested in paper trading, it will be merged into `main` via a Pull Request.

### B. Directory Structure
Instead of creating a completely separate project directory (which fragments Git history and duplicate APIs), we will create a dedicated backend directory inside the existing repository:
```
MarketTerminal/
│
├── index.html                   # Stable trading terminal (frontend cockpit)
├── proxy-server.js              # Stable CORS bypass server
│
└── algo-engine/                 # [NEW] Algorithmic execution backend
    ├── config/                  # Configuration files (API keys, risk thresholds)
    ├── data/                    # Historical data caches and daily GEX profiles
    ├── src/                     # Core execution codebase
    │   ├── calculations.py      # RVOL, Volatility contraction, SMA/EMA calculations
    │   ├── scorecards.py        # MOS-B, MOS-A, MOS-P rubric evaluation
    │   ├── execution.py         # Broker API connectors (Alpaca/IBKR) and order placement
    │   └── server.py            # Local REST/WebSocket API server for index.html cockpit
    └── requirements.txt         # Python dependencies
```
*This architecture keeps the frontend and backend separate, allowing the browser terminal to fetch real-time algorithmic signals and portfolio metrics from a local `algo-engine` service running in the background.*

---

## 2. Staged Implementation Milestones

```
+-------------------------------------------------------------------------------+
|  MILESTONE 1: Data Engine  ==>  MILESTONE 2: Scanners  ==>  MILESTONE 3: Execution  |
+-------------------------------------------------------------------------------+
```

### Milestone 1: Local Data Engine & Calculations (Weeks 1-2)
*   **Deliverables:**
    *   Initialize Python environment and install connectors (Alpaca SDK, Pandas, NumPy).
    *   Build real-time websocket data feeds for regular hours regular candles.
    *   Implement **Time-Slice Premarket RVOL ($RVOL_{TS}$)** and **Regular Hours RVOL ($RVOL_{RM}$)** calculations.
    *   Build daily parser at 08:45 AM to calculate and store options GEX parameters (Put Wall, Call Wall, Flip Level).
*   **Verification:** Run unit scripts comparing calculated RVOLs against manual spreadsheet checks.

### Milestone 2: Scanners & MOS Scorecards (Weeks 3-4)
*   **Deliverables:**
    *   Implement the 15 setups' logic triggers in `src/scorecards.py`.
    *   Build the three tailored scoring rubrics: **MOS-B** (Breakouts), **MOS-A** (VCP/Anticipation), and **MOS-P** (Pullbacks).
    *   Create a local console ticker scanner that prints active trading signals, calculated MOS scores, and catalysts.
*   **Verification:** Verify that a simulated breakout (e.g., SMCI crossing PMH) correctly registers a high MOS-B score ($>8$) and triggers an entry signal in console logs.

### Milestone 3: Risk Management & Alpaca Paper Trading (Weeks 5-6)
*   **Deliverables:**
    *   Connect the engine to Alpaca Paper Trading API.
    *   Implement **Slippage-Protected Buy Stop Limit orders**.
    *   Build the position-sizing logic to dynamically allocate capital based on calculated MOS scores ($0.5\%$, $1.0\%$, or $2.0\%$ risk).
    *   Implement portfolio-wide circuit breakers (3% daily drawdown stop, sector caps, max 5 positions limit).
*   **Verification:** Run the algorithm live in paper trading mode for one week. Confirm that SL and PTP orders are sent instantly upon entry.

### Milestone 4: Cockpit Integration & UI updates (Week 7)
*   **Deliverables:**
    *   Add a local websocket API to the Python engine to stream active logs and metrics.
    *   Modify [index.html](file:///c:/Users/jfan/Documents/MarketTerminal/index.html) in the `feature/algo-integration` branch to connect to this local API.
    *   Add a new **"Algo Execution Control" panel** in the UI, showing active algorithmic positions, current daily P&L, system log streams, and a master **ALGO ON/OFF Kill-Switch**.
*   **Verification:** Launch the engine and open index.html. Verify that the UI displays paper trading logs, active orders, and GEX levels.

---

## 3. Open Questions for User Review

> [!IMPORTANT]
> Please review and provide feedback on these key operational decisions:
> 1. **Preferred Broker API:** Do you prefer using **Alpaca** (developer-friendly, excellent paper trading) or **Interactive Brokers (IBKR)** (broader asset availability, but more complex API setup)?
> 2. **Core Language:** Is **Python** acceptable for the backend `algo-engine`? It is the industry standard for mathematical models, calculations, and broker SDKs.
> 3. **Manual Approval vs. Full Autonomy:** For the first stages, do you want a "Semi-Automated" mode (the algo scans and calculates, but you must click "Approve" in the browser cockpit to execute) or "Fully Automated" mode from day one?

---

## 4. Verification Plan

1.  **Dry Run Backtest:** Run the calculations module against historical data for SMCI and NVDA to verify $RVOL_{RM}$ accuracy at 09:45 AM.
2.  **Order Placement Integrity:** Verify that a Stop Limit order is placed at the exact PMH + 0.25% limit ceiling, and rejects if the gap is skipped.
3.  **Circuit Breaker Stress Test:** Simulate a portfolio drop of 3% in paper mode and verify that the engine triggers immediate market sell orders on all positions and halts trading.
