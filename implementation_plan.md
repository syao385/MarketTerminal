# Implementation Plan - Aether Momentum Algorithmic Trading System (Phase 3)

This plan describes the architectural strategy, staged milestones, and design choices to implement the 15-setup momentum trading playbook as a highly flexible, transparent, and backtestable execution engine.

---

## 1. Project Organization: Versioning & Branching Strategy

To keep the existing production visual terminal ([index.html](file:///c:/Users/jfan/Documents/MarketTerminal/index.html)) fully functional and stable for daily trading, we will develop inside a **new Git branch**:

### A. Git Branching Model
*   **Branch Name:** `feature/algo-integration`
*   **Methodology:** All development for the algorithmic engine occurs in this branch. Once fully tested in paper trading, it will be merged into `main` via a Pull Request.

### B. Directory Structure
Instead of creating a completely separate project directory, we will create a dedicated backend directory inside the existing repository:
```
MarketTerminal/
│
├── index.html                   # Stable trading terminal (frontend cockpit)
├── proxy-server.js              # Stable CORS bypass server
│
└── algo-engine/                 # [NEW] Algorithmic execution backend
    ├── config/                  # Configuration files (API keys, risk thresholds, setup params)
    ├── data/                    # Historical caches and GEX profiles
    ├── src/                     # Core execution codebase
    │   ├── calculations/        # RVOL, Volatility contraction, SMA/EMA calculations
    │   ├── setups/              # Modular setup registry
    │   │   ├── base.py          # Base Setup abstract class
    │   │   ├── setup_1.py       # Gap and Go class
    │   │   ├── setup_12.py      # Standard ORB class
    │   │   └── ...              # Outlines for remaining 13 setups
    │   ├── backtest/            # Backtester and parameter optimizer
    │   │   ├── engine.py        # Reusable backtesting loop
    │   │   └── optimizer.py     # Parameter sweep optimizer (SL, target, RVOL tuning)
    │   ├── execution/           # Broker API connectors (Alpaca SDK)
    │   │   └── alpaca.py        # Alpaca execution with custom client_order_id tagging
    │   └── server.py            # Local REST/WebSocket API server for index.html cockpit
    └── requirements.txt         # Python dependencies
```

---

## 2. Key Design Specifications

### A. Modular Setup Registry (Flexibility)
To ensure the 15 setups can easily evolve, we will use a registry pattern. Every setup inherits from a base class:
```python
class BaseSetup:
    def __init__(self, params: dict):
        self.params = params  # e.g., {'stop_loss_pct': 0.015, 'target_pct': 0.03, 'rvol_threshold': 1.5}
        
    def check_trigger(self, data: pd.DataFrame) -> bool:
        """Returns True if setup trigger conditions are met."""
        raise NotImplementedError
        
    def calculate_mos(self, data: pd.DataFrame) -> float:
        """Evaluates the setup's tailored scoring scorecard."""
        raise NotImplementedError
```
All parameters are stored in a configuration file (`config/setups.yaml`). You can adjust thresholds (e.g., changing ORB window or VCP contraction counts) without touching the code.

### B. Reusable Backtest & Parameter Optimizer (Tuning)
*   **Engine (`backtest/engine.py`):** Runs historical simulations on day/intraday candles.
*   **Optimizer (`backtest/optimizer.py`):** Runs automated parameter sweeps (e.g., testing stop-losses from $0.5\%$ to $3.0\%$ in $0.1\%$ increments) to output optimal win rates, profit factors, and Sharpe ratios for each setup.
*   **Journaling & Alpaca Tags:** When executing trades, the engine generates a tagged `client_order_id`:
    `client_order_id = f"AETHER_{setup_id}_{timestamp}"`
    Alpaca's execution reporting carries this ID, which is automatically saved to a local SQLite/JSON journal database for historical performance auditing.

### C. Transparency & Visual Validation (No Black Box)
To avoid black-box execution, the engine exposes all underlying data:
1.  **UI Detail Panel:** The frontend dashboard will display the exact scorecard calculations (e.g., `Catalyst: +3.0, Vol: +2.5, GEX: +1.5 = MOS 9.0`).
2.  **Visual Validation Export:** The engine will export trade triggers and historical indicators to a standard CSV format configured for easy copy-pasting/importing into **TradingView** or **ThinkOrSwim** charts.
3.  **Lightweight Chart Integration:** In Milestone 4, we will embed a lightweight charting utility in the UI that highlights GEX levels, VWAP, EMA lines, and execution marker points.

---

## 3. Staged Implementation Milestones

```
+-------------------------------------------------------------------------------------+
|  MILESTONE 1: Data Engine  ==>  MILESTONE 2: Scanners/Backtest  ==>  MILESTONE 3: Execution  |
+-------------------------------------------------------------------------------------+
```

### Milestone 1: Local Data Engine & Calculations (Weeks 1-2)
*   **Deliverables:**
    *   Initialize Python env, configure `config/setups.yaml` and Alpaca API.
    *   Build websocket data feeds for regular hours candles.
    *   Implement Time-Slice Premarket RVOL ($RVOL_{TS}$) and Regular Hours RVOL ($RVOL_{RM}$).
    *   Set up daily 08:45 AM option GEX parser.
*   **Verification:** Run checks to confirm RVOL and GEX output matches local records.

### Milestone 2: Setup Registry, Scanners & Backtester (Weeks 3-4)
*   **Deliverables:**
    *   Build `BaseSetup` and implement the 15 setups using YAML parameters.
    *   Implement the 3 tailored scorecards (**MOS-B**, **MOS-A**, **MOS-P**).
    *   Implement `backtest/engine.py` and `optimizer.py` for parameter tuning.
    *   Build visual CSV exporters for TradingView validation.
*   **Verification:** Run optimization sweeps on historical data to check setup profitability.

### Milestone 3: Order Execution & Alpaca Integration (Weeks 5-6)
*   **Deliverables:**
    *   Connect `execution/alpaca.py` to Alpaca Paper Trading.
    *   Implement Stop Limit order execution with 0.25% slippage controls.
    *   Apply dynamic sizing based on MOS score ($0.5\%$, $1.0\%$, or $2.0\%$ risk).
    *   Implement portfolio-wide constraints (3% daily limit, sector caps, 5 active trades limit).
    *   Add setup-tagged `client_order_id` journaling.
*   **Verification:** Run paper trading simulation to confirm tag-grouped orders are executed correctly.

### Milestone 4: Cockpit Integration & Charting Panel (Week 7)
*   **Deliverables:**
    *   Build websocket server to stream live calculations and logs.
    *   Add the **"Algo Execution Control"** dashboard in `index.html`.
    *   Integrate a lightweight charting window to visualize candles, GEX walls, and execution signals.
*   **Verification:** Final end-to-end dry run.

---

## 4. Verification Plan

1.  **Backtest Sweep Verification:** Run the optimizer to check that tuning suggestions correspond to correct trade stats.
2.  **Order Tag Audit:** Fetch Alpaca execution logs to verify orders carry correct `AETHER_{setup_id}` tags.
3.  **Visualization Audit:** Check that GEX walls and entry indicators align with TradingView charts.
