# Institutional Momentum & Algorithmic Trading Playbook
## Integrating Option GEX, Cumulative Delta, and Advanced Volume Signature Analysis

This playbook defines the quantitative framework, calculations, and rules for identifying, scoring, and executing high-probability momentum setups. It serves as the functional specification for transitioning the Aether Market Terminal into an automated algorithmic trading system.

---

## 1. Advanced Volume Signature: Institutional Premarket RVOL

In institutional trading, absolute premarket volume (e.g., 300k shares) is secondary to **Relative Volume (RVOL)**. A large-cap stock trading 500k shares in premarket might represent normal liquidity, whereas a mid-cap stock trading 500k shares represents a massive institutional footprint.

### A. The Calculations

Institutions utilize two primary calculations to normalize premarket volume:

#### 1. Time-Slice Relative Volume ($RVOL_{TS}$)
Premarket volume is highly time-dependent. To avoid time-of-day distortion, volume is measured relative to the historical average *at that exact time slice*:

$$RVOL_{TS}(t) = \frac{\text{Cumulative Vol from 04:00 AM to time } t \text{ today}}{\text{Mean Cumulative Vol from 04:00 AM to time } t \text{ over last } 20 \text{ days}}$$

*   **Thresholds:**
    *   $RVOL_{TS} > 3.0$: Heavy institutional accumulation (catalyst-driven).
    *   $1.5 \le RVOL_{TS} \le 3.0$: Active retail/institutional interest.
    *   $RVOL_{TS} < 1.0$: Illiquid, thin, high-risk spread.

#### 2. Premarket to Average Daily Volume Ratio ($Vol_{PM}/ADV$)
This metric measures the percentage of the 30-day Average Daily Volume (ADV) traded *before the opening bell*:

$$\text{PM/ADV Ratio} = \frac{\text{Total Volume traded from 04:00 AM to 09:30 AM today}}{\text{30-Day Average Daily Volume (ADV)}}$$

*   **Thresholds:**
    *   **$\text{PM/ADV Ratio} \ge 5\%$:** Historic institutional block positioning (indicates a high-probability **Episodic Pivot**).
    *   **$2\% \le \text{PM/ADV Ratio} < 5\%$:** High-conviction Gap and Go candidate.
    *   **$\text{PM/ADV Ratio} < 1\%$:** Low-conviction, retail-dominated gap; high probability of fading.

---

## 2. Option GEX & Order Flow Confluence

By integrating options market maker positioning (dealers' hedging constraints) and order flow, we establish structural boundaries and execution triggers:

### A. Volatility Regimes via GEX Flip
*   **Negative Gamma Regime (Below GEX Flip):** Dealers hedge by selling on price drops and buying on price rises, structurally **accelerating volatility**. Breakout strategies have a much higher success rate in this regime because dealer hedging loops feed the trend.
*   **Positive Gamma Regime (Above GEX Flip):** Dealers hedge by buying on price drops and selling on price rises, **suppressing volatility**. Breakouts are continuously absorbed, making mean reversion strategies the dominant setup.

### B. Micro-Order Flow Triggers
*   **Cumulative Delta Trend:** Shows the cumulative difference between market buy and market sell orders:
    $$\text{Cumulative Delta} = \sum (\text{Aggressive Buys} - \text{Aggressive Sells})$$
    A vertical delta line confirms aggressive buyers are taking liquidity, supporting a breakout.
*   **Liquidity Pulling (DOM):** Prior to a breakout, resting limit orders on the ask ladder disappear (pull), signaling that passive sellers are stepping out of the way.
*   **Stacked Imbalances (Footprint):** Three or more consecutive price bars printing diagonal buying imbalances ($\ge 3.5\times$ bid size) confirm aggressive institutional sweeps.

---

## 3. The 11 Institutional Momentum Trading Setups

### Setup 1: Gap and Go (Intraday Breakout)
*   **Trigger / Scanner Condition:** Premarket Gap $>5\%$, PM volume $>100,000$ shares, $RVOL_{TS} > 1.5$, with an opening 5-minute candle closing green above the Premarket High (PMH).
*   **Stop-Loss:** Low of the first 5-minute candle (Opening Range Low - ORL).
*   **Target:** GEX Call Wall or $+2$ Standard Deviation price band.
*   **Partial Take-Profit (PTP) Plan:** Sell 50% at $1.5\text{R}$ (where $\text{R}$ is the initial risk distance) and trail the remaining 50% with the 9 EMA. Move stop-loss to breakeven after PTP 1.

### Setup 2: Gap and Fade (Intraday Reversal)
*   **Trigger / Scanner Condition:** Premarket Gap $>5\%$ but on weak volume ($RVOL_{TS} < 1.0$ and $\text{PM/ADV Ratio} < 1\%$). Price opens near PMH or GEX Call Wall and fails, closing back below PMH on a 1-minute chart with Cumulative Delta flattening and Sonar Pulse Ratio $< 0.15$.
*   **Stop-Loss:** High of Day (HOD) + 5 cents.
*   **Target:** GEX Flip Level or Premarket Low (PML).
*   **Partial Take-Profit (PTP) Plan:** Sell 50% at $1.5\text{R}$, move stop to breakeven, and cover the remaining 50% at the GEX Flip Level.

### Setup 3: Episodic Pivot (EP / Momentum Burst)
*   **Trigger / Scanner Condition:** Price gaps $>8\%$ out of a consolidation range on historic volume ($\text{PM/ADV Ratio} \ge 5\%$) driven by a Tier 1 catalyst (Earnings, regulator clearance, auditor change). Entry on a breakout above the daily 50-day resistance pivot.
*   **Stop-Loss:** Low of the EP Day (LOD).
*   **Target:** $+4$ to $+6$ Average True Range (ATR) extension.
*   **Partial Take-Profit (PTP) Plan (3-Tier):** Sell 40% at $2\text{R}$, sell 30% at $4\text{R}$, and trail the final 30% using the daily 9-day EMA.

### Setup 4: Red-to-Green (R2G) Intraday Reversal
*   **Trigger / Scanner Condition:** Open price is below yesterday's close. Ticker rallies and crosses above yesterday's close on expanding volume ($RVOL_{TS} > 1.5$) with Cumulative Delta trending up.
*   **Stop-Loss:** Low of Day (LOD).
*   **Target:** Premarket High (PMH).
*   **Partial Take-Profit (PTP) Plan:** Sell 50% at yesterday's close + $1.5\text{R}$, and trail the rest to the PMH.

### Setup 5: VWAP Institutional Hold & Re-Entry
*   **Trigger / Scanner Condition:** Active stock in a strong daily uptrend pulls back to touch VWAP (within 0.1% buffer). Large limit buy orders stack on the DOM at VWAP, followed by a 1-minute close green away from VWAP.
*   **Stop-Loss:** VWAP - 5 cents.
*   **Target:** High of Day (HOD).
*   **Partial Take-Profit (PTP) Plan:** Sell 50% at $1.5\text{R}$ (or near HOD) and trail the remaining 50% with VWAP as a trailing stop.

### Setup 6: Gamma Squeeze / Short Squeeze Sweep
*   **Trigger / Scanner Condition:** Short Interest $>15\%$ or high call option volume anomaly. Price crosses GEX Flip Level into negative gamma with delta velocity spiking ($ROC > 2.0$).
*   **Stop-Loss:** GEX Flip Level - 10 cents.
*   **Target:** $+2$ Standard Deviation price expansion target.
*   **Partial Take-Profit (PTP) Plan:** Sell 40% at $2\text{R}$, sell 30% at $4\text{R}$, and trail the remaining 30% until a reversal bar prints on the 5-minute chart.

### Setup 7: Day 2/3 Momentum Continuation
*   **Trigger / Scanner Condition:** Day 1 was a verified Episodic Pivot (EP). Day 2 opens without an excessive gap ($<4\%$ from Day 1 close) and breaks above the Day 1 High on morning volume $>1.5\times$ historical morning average.
*   **Stop-Loss:** Day 2 Low of Day (LOD).
*   **Target:** $+2$ ATR extension of the Day 1 high.
*   **Partial Take-Profit (PTP) Plan:** Sell 50% at $2\text{R}$, move stop to breakeven, and trail the remainder with the daily 9-EMA.

### Setup 8: High Tight Flag (HTF)
*   **Trigger / Scanner Condition:** Price gained $\ge 100\%$ in the last 30 trading days. Price consolidates sideways within a tight flag range ($\le 25\%$ depth) for 5 to 15 trading days. Entry on a daily close breaking out above the flag high on volume $>2\times$ average.
*   **Stop-Loss:** Low of the flag consolidation range.
*   **Target:** $+50\%$ extension from the flag breakout point.
*   **Partial Take-Profit (PTP) Plan:** Sell 50% at $3\text{R}$ (swing breakout target), and trail the remaining 50% using the daily 10-EMA.

### Setup 9: Volatility Contraction Pattern (VCP) / Cup & Handle Pivot
*   **Trigger / Scanner Condition:** Stock in Stage 2 uptrend ($Price > 150 > 200$ EMA). Price exhibits 2 to 4 distinct contractions in price volatility (e.g., $20\% \rightarrow 10\% \rightarrow 4\%$). Volume dries up to $<50\%$ of ADV on the final contraction. Entry on a breakout above the contraction pivot on volume $>2\times$ average.
*   **Stop-Loss:** Low of the last contraction wave.
*   **Target:** $+30\%$ extension from the pivot breakout.
*   **Partial Take-Profit (PTP) Plan:** Sell 40% at $2\text{R}$, sell 30% at $4\text{R}$, and trail the final 30% using the daily 21-EMA.

### Setup 10: 10/21 EMA Short-Term Trend Pullback (The Momentum Glide)
*   **Trigger / Scanner Condition:** Stock is in a strong Stage 2 uptrend ($Price > 10\text{ EMA} > 21\text{ EMA} > 200\text{ SMA}$). Price pulls back to touch either the 10 EMA or 21 EMA. Entry is triggered when a candle closes green reclaiming/bouncing off the EMA on volume greater than the previous 3 candles.
*   **Stop-Loss:** Daily close below the 21 EMA by more than 1%.
*   **Target:** Prior swing high or $+1.5$ ATR extension.
*   **Partial Take-Profit (PTP) Plan:** Sell 50% at the prior swing high (or $1.5\text{R}$), move stop-loss of the remaining shares to breakeven, and trail the rest along the 21 EMA.

### Setup 11: 50 SMA Institutional Support Bounce
*   **Trigger / Scanner Condition:** Stock is in a primary Stage 2 uptrend ($Price > 50\text{ SMA} > 200\text{ SMA}$). Price pulls back to the 50 SMA on declining volume and contracting volatility. Reversal trigger is fired when a daily candle closes green (e.g., hammer or engulfing pattern) at the 50 SMA on volume $>1.5\times$ average.
*   **Stop-Loss:** Daily close below the 50 SMA by more than 1.5% or below the low of the reversal candle.
*   **Target:** Previous major swing high.
*   **Partial Take-Profit (PTP) Plan:** Sell 40% at the previous swing high, sell 30% at $+2$ standard deviations, and trail the final 30% along the 50 SMA.

---

## 4. The Unified Momentum Opportunity Scorecard (MOS)

Before executing any trade, score the setup using this **10-point quantitative rubric**:

| Category | Factor Checked | Condition | Score |
| :--- | :--- | :--- | :--- |
| **1. Catalyst** | Quality & Recency | **Tier 1:** Earnings blowout, FDA approval, major contract, or auditor change.<br>**Tier 2:** Analyst upgrade, sector momentum, general news.<br>**Tier 3:** Technical gap only, stale news (>24h), or "No catalyst" found. | **+3 pts**<br>**+1 pt**<br>**+0 pts** |
| **2. Volume** | Relative Strength | **Historic:** $RVOL_{TS} > 3.0$ AND $\text{PM/ADV Ratio} \ge 5\%$.<br>**Standard:** $RVOL_{TS} \ge 1.5$ OR $\text{PM/ADV Ratio} \ge 2\%$.<br>**Weak:** $RVOL_{TS} < 1.0$ AND $\text{PM/ADV Ratio} < 1\%$. | **+2 pts**<br>**+1 pt**<br>**-1 pt** |
| **3. Vol Regime** | Option GEX Profile | **Negative Gamma:** Price is below GEX Flip Level (volatility expansions).<br>**Positive Gamma:** Price is above GEX Flip Level (volatility dampening). | **+1 pt**<br>**-1 pt** |
| **4. Order Flow** | Cumulative Delta | **Sweep:** Cumulative Delta trending sharply with price; Ask liquidity pulling.<br>**Absorption:** Delta rising but price flat at GEX Wall (exhaustion). | **+1 pt**<br>**-1 pt** |
| **5. Technicals** | Key Levels | **Breakout:** Price closes above Premarket High (PMH) & GEX Flip.<br>**Range-Bound:** Price is trapped inside PMH-PML range.<br>**Breakdown:** Price breaks below Premarket Low (PML). | **+3 pts**<br>**+0 pts**<br>**-3 pts** |

---

## 5. Risk Management & Execution Matrix

Position sizing is dynamically adjusted based on the quantitative **MOS Score** to preserve capital and maximize edge.

### A. Position Sizing & Allocation

| MOS Score | Opportunity Conviction | Risk per Trade (R) | Equity Allocation |
| :--- | :--- | :--- | :--- |
| **9 - 10** | High-Conviction Breakout (Tier 1) | **2.0%** of account equity | **100%** of standard unit size |
| **7 - 8** | Moderate Momentum (Tier 2) | **1.0%** of account equity | **50%** of standard unit size |
| **5 - 6** | Low-Conviction / Tactical (Tier 3) | **0.5%** of account equity | **25%** of standard unit size |
| **< 5** | Unfavorable (Do Not Trade Long) | **0.0%** | **No Entry** (or Short Fade only) |

### B. Execution Rules
1.  **Stop-Loss discipline:** Stop-losses are hard-coded on entry. No manual adjustment of stops lower is permitted.
2.  **Breakeven Adjustments:** For all breakout plays (Setups 1, 3, 4, 7, 8, 9), once Partial Take-Profit 1 (PTP 1) is achieved, the stop-loss of the remaining position **must be moved to the entry price (breakeven)**.
3.  **Slip Management:** Slippage must be monitored. If execution slippage exceeds 0.5% of the entry price, size down by 50% for subsequent entries on that ticker to protect risk parameters.
