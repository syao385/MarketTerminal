# Aether Market Terminal - Professional User Guide & Decision Workflows

**Document Version:** 2.0.0  
**Status:** Approved / Production-Current  
**Last Architectural Review:** September 2026  
**Target Audience:** Algorithmic Traders, Portfolio Managers, Quantitative Researchers  

---

## Document Revision History

| Version | Date | Author / Team | Summary of Changes |
| :--- | :--- | :--- | :--- |
| **v1.0.0** | July 2026 | Quantitative Dev Team | Initial release: TradingView widget, Gemini AI analyst, sentiment meters, and paper trade simulator. |
| **v1.1.0** | July 2026 | Systems Architecture | Added central yfinance proxy, premarket gapper batch catalyst prompts, and weekly ETF flow Z-scores. |
| **v2.0.0** | September 2026 | Lead Architect & Quant Team | **Major Production Release:** Custom dual-pane HTML5 canvas chart (SMAs, GEX walls, FVGs, unmitigated gaps, CVD line), 30-thread parallel scanner (260+ tickers, 15 setups), SQLite persistent trade journal (	rading_system.db), historical backtester & parameter sweep optimizer, and watchlist warning badges (⚠️ Count (MOS)). |

---

## 0. Multi-Project System Architecture, Port Registry & Startup Sequence

When your computer reboots or when launching the trading systems, follow the sequence below:

`mermaid
graph TD
    A["Computer Reboots / System Startup"] --> B["Master One-Click Launcher<br>C:\Users\jfan\Documents\launch_all_terminals.bat"]
    
    B --> C["Step 1: Launches GammaGexTrading (run.bat on Port 8000)"]
    B --> D["Step 2: Launches MarketTerminal (run_backend.bat on Port 8080)"]
    
    C --> E["Access Desk 1: http://127.0.0.1:8000"]
    D --> F["Access Desk 2: http://127.0.0.1:8080"]
    
    F --> G["MarketTerminal Engine (Port 8080) Handles Central yfinance Proxy, Scanner, Journal DB & Web UI"]
    E --> H["GammaGexTrading Engine (Port 8000) Handles Options Gamma GEX Desk"]
    G -- "Cross-Queries GEX Levels" --> E
`

### Complete Port & URL Directory

| Trading Project | Local Service URL | Port | Launcher Script Path | Project Functionality |
| :--- | :--- | :--- | :--- | :--- |
| **MarketTerminal Cockpit** | **http://127.0.0.1:8080** | **8080** | un_backend.bat | **Main Algorithmic Trading Terminal**. Hosts Web UI (/), Central yfinance Candlestick Proxy (/api/candles), Indicators (/api/metrics), Universal Scanner (/api/scanner), Database Journal (/api/journal), and Backtesting Lab. |
| **GammaGexTrading Desk** | **http://127.0.0.1:8000** | **8000** | ../GammaGexTrading/run.bat | **Options Gamma GEX Desk**. Computes zero-gamma, call wall, and put wall levels. MarketTerminal cross-queries Port 8000 for level reuse. |
| **Node RSS Proxy** | **http://127.0.0.1:3000** | **3000** | start-proxy.bat | Proxy server for NAAIM / AAII market sentiment XML feeds. |

---

### How to Launch on System Reboot

#### Method A: Master One-Click Launch (Recommended)
1. Double-click **launch_all_terminals.bat** (or un_backend.bat in the project root).
2. It will automatically start **GammaGexTrading (Port 8000)** and **MarketTerminal (Port 8080)** in sequence and open your browser!

#### Method B: Individual Standalone Launch
- **To launch MarketTerminal alone**:
  1. Open folder MarketTerminal\.
  2. Double-click **un_backend.bat**.
  3. Access Web UI at **http://127.0.0.1:8080**.
- **To launch GammaGexTrading alone**:
  1. Open folder GammaGexTrading\.
  2. Double-click **un.bat**.
  3. Access Web UI at **http://127.0.0.1:8000**.

---

## 1. Centralized Backend yfinance Proxy & Cache Architecture

To eliminate Yahoo Finance usage limits and 429 rate errors:

1. **Central In-Memory Cache (CANDLE_CACHE)**: MarketTerminal engine on port 8080 maintains a 120-second (2-minute) TTL cache.
2. **Unified Proxy Endpoint (GET /api/candles)**:
   - Both the browser UI (index.html) and python background engines (scanner.py, metrics.py, acktester.py) request candlestick bars via http://127.0.0.1:8080/api/candles.
   - On cache hits ($< 120), data is delivered in **$< 1\text{ms}$** with zero outbound Yahoo Finance network requests.
   - Cache misses trigger a single polite upstream request and cache the returned bars for all other callers.

---

## 2. Interactive Dual-Pane HTML5 Canvas Charting Engine

The terminal features a custom-built, hardware-accelerated HTML5 dual-pane canvas chart that eliminates heavy external iframe dependencies while delivering institutional-grade indicators:

`
+---------------------------------------------------------------------------------------------+
| TOP PANE (72% Height): Price Candlesticks, SMAs, GEX Boundaries, Gaps, FVGs                 |
|  - Candlesticks: Green / Red with high/low wicks                                           |
|  - Moving Averages: SMA 20 (Blue), SMA 50 (Orange), SMA 200 (Purple)                       |
|  - Options GEX Levels: Call Wall (Green line), Put Wall (Red line), Zero-Gamma (Gold line) |
|  - Unmitigated Daily Gaps: Transparent horizontal price zones spanning across history       |
|  - Fair Value Gaps (FVG): 3-candle imbalance zones (Bullish green, Bearish red)            |
+---------------------------------------------------------------------------------------------+
| BOTTOM PANE (23% Height): Volume Pacing & Cumulative Volume Delta (CVD)                     |
|  - Volume Bars: Color-coded by buyer/seller control and RVOL intensity                     |
|    * RVOL < 1.0: Muted / Faded Gray                                                         |
|    * RVOL 1.0 - 2.0: Standard Session Volume                                                |
|    * RVOL 2.0 - 3.0: High-Intensity Neon Green / Red (Setup Trigger)                        |
|    * RVOL > 3.0: Climax Institutional Volume (Electric Magenta / Gold)                     |
|  - Cumulative Volume Delta (CVD): Bright Cyan running flow line of aggressive delta pressure |
+---------------------------------------------------------------------------------------------+
`

### Timeframe Selectors
Use the timeframe selector buttons above the chart to dynamically recompute all indicators:
- **1D (Daily):** Macro trend analysis, SMA 50/200, daily unmitigated gaps, episodic pivots.
- **1H (Hourly):** Multi-day swing structure, intermediate FVG zones.
- **5M (5-Minute):** Primary intraday execution timeframe for ORBs, Gap & Go, and VWAP holds.
- **1M (1-Minute):** Micro-order flow, high-velocity volume acceleration sweeps ({Vol}$).

---

## 3. Playbook Scanner Cockpit & The 15 Setups

The **Playbook Scanner Cockpit** is located directly below the chart, providing complete coverage of all 15 institutional momentum setups across the 260+ ticker universe:

### The 15 Setups Matrix

| Setup ID | Setup Name | Category | Primary TF | Score Model | Strategic Concept |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Setup 1** | Gap and Go | Breakout | 5m | MOS-B | Intraday breakout above Premarket High on heavy catalyst volume. |
| **Setup 2** | Gap and Fade | Pullback | 5m | MOS-P | Short reversal on low-volume gaps lacking catalyst support. |
| **Setup 3** | Episodic Pivot (EP) | Breakout | 1d / 5m | MOS-B | Multi-week institutional accumulation on massive earnings blowout. |
| **Setup 4** | High-Tight Flag (HTF)| Breakout | 1d / 5m | MOS-B | Breakout from tight consolidation after 100%+ run in <4 weeks. |
| **Setup 5** | VWAP Hold & Re-Entry | Pullback | 5m | MOS-P | Intraday pullback holding institutional VWAP benchmark. |
| **Setup 6** | Parabolic Exhaustion | Pullback | 1d / 5m | MOS-P | Counter-trend short on blow-off tops extended 3+ days from 20-EMA. |
| **Setup 7** | Red-to-Green (R2G) | Pullback | 5m | MOS-P | Intraday reclaim of prior day's close triggering algo buy sweeps. |
| **Setup 8** | Second Day Play | Pullback | 1d / 5m | MOS-P | Day 2 morning pullback hold following Day 1 high-volume expansion. |
| **Setup 9** | Volatility Contraction| Basing | 1d | MOS-A | Classic Mark Minervini VCP breakout with dry-up volume. |
| **Setup 10**| 10/21 EMA Pullback | Pullback | 5m | MOS-P | Trend continuation pullback to 10/21 exponential moving average zone. |
| **Setup 11**| 30-Min ORB | Pullback | 15m | MOS-P | Breakout above 30-minute opening range high on .0\times$ RVOL. |
| **Setup 12**| Standard 15-Min ORB | Breakout | 5m | MOS-B | Classic 15-minute Opening Range Breakout with .5\times$ RVOL. |
| **Setup 13**| Blue Sky ATH Breakout| Breakout | 1d | MOS-B | Clean breakout above all historical resistance into all-time highs. |
| **Setup 14**| Stage 1-to-2 Reversal| Basing | 1d | MOS-A | Stan Weinstein Stage 2 breakout reclaiming rising 200-day SMA. |
| **Setup 15**| PEAD Breakout | Breakout | 1d | MOS-B | Post-Earnings Announcement Drift consolidation breakout. |

### Cockpit Navigation
1. **Left Setup Tabs:** Scrollable list of all 15 setups with live trigger counts (e.g. Gap and Go [3]).
2. **Center Triggers Table:** Lists active candidates with Spot Price, Gap %, RVOL, and MOS Score.
   - Click any row to automatically load that ticker onto the main chart and update the scorecard.
3. **Right Scorecard Gauge:** Displays the normalized 10-point MOS rating, conviction tier (Tier 1 / Tier 2 / Tier 3), and point-by-point category breakdown.

---

## 4. Persistent SQLite Setup Journal & Execution Tracking

All trade setups, manual paper trades, and scanner discoveries are persistently logged in a local SQLite database (lgo-engine/data/trading_system.db).

### Setup Journal Tabs (Tab 1)
The left sidebar of the Setup Journal features two coordinated panels:
1. **Today's Triggers:** Displays live triggers detected during today's market session for the selected symbol.
2. **Saved Logs (SQLite):** Historical saved trade logs fetched from the database:
   - Includes page navigation controls (◀ Prev / Page X / Next ▶).
   - Clicking a saved log renders its exact historical scorecard breakdown, logged metrics, entry/stop/target risk parameters, and an inline candlestick thumbnail chart.
   - **Trade Status Dropdown:** Toggle trade outcome directly between **Pending**, **Win**, or **Loss** to record real performance.

### Watchlist Warning Alert Badges
All four watchlists (Personal Watchlist, Portfolio, Top 10 In-Play, Premarket Gappers) feature automated warning badges:
- Format: **⚠️ Count (MOS)** (e.g. ⚠️ 2 (8.5))
- **Count:** Number of active playbook setups currently triggering on that ticker.
- **MOS:** Highest Opportunity Scorecard rating computed for that ticker.
- Clicking any badge instantly opens the **Setup Journal** tab and focuses the candidate ticker.

---

## 5. Historical Backtester & Parameter Sweep Optimizer

The terminal includes an institutional simulation engine to test setups against historical price data before risking live capital.

### Running Historical Backtests (/api/backtest)
1. Select a symbol (e.g. NVDA) and setup (e.g. setup_12).
2. The backtester evaluates historical price candles bar-by-bar:
   - Sizes positions using the Kelly Criterion based on the MOS score.
   - Implements multi-stage exits: sells 50% at Target 1 (1.5R) and moves stop to breakeven.
   - Exits remaining 50% at Target 2 (3.0R) or on trailing stop hits.
   - Outputs: Initial Capital, Final Capital, Net Profit, Win Rate, Profit Factor, and Max Drawdown.

### Parameter Sweep Optimizer (/api/optimize)
- Runs automated grid-search sweeps across parameter ranges (e.g.  \in [1.0, 1.5, 2.0, 2.5]$, $\text{Profit Target} \in [1.5, 2.0, 3.0, 4.0]$).
- Identifies optimal parameter combinations that maximize net returns and profit factors on that asset.

---

## 6. Trading Session Routine: When and How Often to Use

| Session / Time | Focus Area | Dashboard Widget to Check | Objective / Trading Action |
| :--- | :--- | :--- | :--- |
| **Premarket**<br>*(8:00 - 9:30 AM EST)* | Catalyst discovery & gap scan | Premarket Gappers, Top 10 In-Play | Identify gapping stocks with fresh catalysts; check RVOL_TS; identify Setup 1 & 2 candidates. |
| **Market Open**<br>*(9:30 - 10:30 AM EST)* | Technical execution & momentum | Dual-Pane Canvas Chart, Scanner Cockpit | Monitor 15-minute ORB (Setup 12); check RVOL_RM at 09:45 AM; enter on confirmed breakouts. |
| **Mid-day**<br>*(10:30 AM - 3:30 PM EST)* | Position management & pullbacks | Setup 5 (VWAP Hold), Setup 10 (EMA Pullback) | Run Gemini Analyst on open positions; check CVD flow line; trim winners at Target 1 (1.5R). |
| **Market Close**<br>*(3:30 - 4:00 PM EST)* | Bookkeeping & daily wrap-up | Setup Journal, Portfolio & History | Update trade status (Win/Loss) in SQLite database; review portfolio equity and daily P&L. |
| **Weekend / Weekly Close**<br>*(Friday pm - Sunday)* | Macro positioning & backtesting | Macro Flows, Backtest Lab, Setups 13, 14, 15 | Run parameter sweeps on upcoming setups; review NAAIM/AAII positioning; build swing list. |

---

## 7. Institutional Decision Flowchart

`mermaid
flowchart TD
    Start([Start Trading Session]) --> TimeCheck{What Session Is It?}
    
    %% Premarket Session
    TimeCheck -- "Premarket (8:00 - 9:30 AM)" --> PM1[Scan Premarket Gappers]
    PM1 --> PM2{Catalyst & Vol Check}
    PM2 -- "Gap > 5%, Vol > 50k, Fresh Catalyst" --> PM3[Add to Long Watchlist (Setup 1)]
    PM2 -- "Gap > 5%, Vol > 50k, Faded Catalyst" --> PM4[Flag for Gap & Fade Short (Setup 2)]
    PM2 -- "No Gappers" --> PM5[Review Top 10 In-Play Tickers]
    
    %% Market Open
    TimeCheck -- "Market Open (9:30 - 10:30 AM)" --> MO1[Monitor 15-Minute ORB at 09:45 AM]
    MO1 --> MO2{RVOL_RM Check}
    MO2 -- "RVOL_RM >= 4.0" --> MO3[High Conviction Breakout - Enter Full Size]
    MO2 -- "2.0 <= RVOL_RM < 4.0" --> MO4[Moderate Conviction - Enter 50% on Pullback Hold]
    MO2 -- "RVOL_RM < 1.5" --> MO5[Failed Volume - Stand Aside or Fade]
    
    %% Mid-Day
    TimeCheck -- "Mid-Day (10:30 AM - 3:30 PM)" --> MD1[Monitor CVD Flow Line & VWAP Holds]
    MD1 --> MD2{Price at Target 1 (1.5R)?}
    MD2 -- "Yes" --> MD3[Sell 50% Size, Move Stop to Breakeven]
    MD2 -- "No" --> MD4[Trail with 10 EMA / 21 EMA]
    
    %% Market Close
    TimeCheck -- "Market Close (3:30 - 4:00 PM)" --> MC1[Update SQLite Trade Journal Status]
    MC1 --> MC2[Review Realized P&L and Risk Metrics]
    
    %% Weekend / Off-Hours
    TimeCheck -- "Weekend / Off-Hours" --> WE1[Refresh Macro Flows & Surveys Dashboard]
    WE1 --> WE2{Analyze NAAIM & AAII Positioning}
    WE2 -- "AAII Bullish > 50% & NAAIM > 100%" --> WE3[Sell Signal: High Hedging / Raise Cash]
    WE2 -- "AAII Bearish > 50% & NAAIM < 30%" --> WE4[Buy Signal: Begin Long Accumulation]
    WE2 -- "Normal range" --> WE5[Check ETF Weekly Flows Z-Scores]
`

---

## 8. Alpaca API Configuration & Settings Management

To connect the terminal to your Alpaca Paper Trading account:
1. Click the **Gear (⚙️)** icon in the top-right header to open the Settings modal.
2. Enter your **Alpaca API Key ID** (e.g. PK6MNM...).
3. Enter your **Alpaca Secret Key**.
4. Click **Save Settings**.
5. The frontend synchronizes credentials with POST /api/settings on the FastAPI backend, saving them securely to lgo-engine/config/alpaca_config.json.
6. Position sizing and trade order tags (AETHER_{setup_id}_{timestamp}) are automatically tracked.

---

## 9. System Troubleshooting & Reboot Procedures

| Symptom | Probable Cause | Corrective Action |
| :--- | :--- | :--- |
| **Port 8080 already in use** | Stale Python or uvicorn process from a prior session. | Run un_backend.bat. The script automatically detects and terminates any process listening on 8080. |
| **Options GEX lines missing** | GammaGexTrading server on Port 8000 is offline. | Start GammaGexTrading/run.bat. The chart will automatically query Port 8000 on the next refresh. If unavailable, local fallback math will be used. |
| **Candlestick chart empty** | Internet disconnection or Yahoo Finance transient glitch. | Check network connection. The backend cache will automatically refresh upon internet restoration. |
| **Scanner returns 0 results** | Market is closed and premarket criteria are not met. | Run the scanner during active market hours (04:00 - 16:00 EST) or test historical setups in the Backtester. |
