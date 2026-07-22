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

## 2. Volatility Regimes & Order Flow Confluence

By integrating options market maker positioning (dealers' hedging constraints) and order flow, we establish structural boundaries and execution triggers:

### A. Volatility Regimes via GEX Flip
*   **Negative Gamma Regime (Below GEX Flip):** Dealers hedge by selling on price drops and buying on price rises, structurally **accelerating volatility**. Breakout strategies have a much higher success rate in this regime because dealer hedging loops feed the trend.
*   **Positive Gamma Regime (Above GEX Flip):** Dealers hedge by buying on price drops and selling on price rises, **suppressing volatility**. Breakouts are continuously absorbed, making mean reversion and pullback strategies the dominant setups.

### B. Micro-Order Flow Triggers
*   **Cumulative Delta Trend:** Shows the cumulative difference between market buy and market sell orders:
    $$\text{Cumulative Delta} = \sum (\text{Aggressive Buys} - \text{Aggressive Sells})$$
    A vertical delta line confirms aggressive buyers are taking liquidity, supporting a breakout.
*   **Liquidity Pulling (DOM):** Prior to a breakout, resting limit orders on the ask ladder disappear (pull), signaling that passive sellers are stepping out of the way.
*   **Stacked Imbalances (Footprint):** Three or more consecutive price bars printing diagonal buying imbalances ($\ge 3.5\times$ bid size) confirm aggressive institutional sweeps.

---

## 3. The 15 Momentum Trading Setups (By Category)

To achieve maximum quantitative accuracy, the 15 setups are divided into **three functional categories**, each with its own structural requirements, triggers, stops, targets, and exit rules.

---

### Category A: Breakout & Momentum Shock Setups (MOS-B)
*These setups exploit volatility expansion, catalyst surprises, and dealer hedging loops. They require high volume and clear directional momentum to succeed.*

#### Setup 1: Gap and Go (Intraday Breakout)
*   **Concept:** Buying a stock gapping up on a positive catalyst that breaks above its premarket high.
*   **Trigger / Scanner Condition:** Premarket Gap $>5\%$, PM volume $>100k$ shares, $RVOL_{TS} > 1.5$. Entry is triggered when the opening 5-minute candle closes green above the Premarket High (PMH).
*   **Stop-Loss:** Low of the first 5-minute candle (Opening Range Low - ORL).
*   **Target:** GEX Call Wall or $+2$ Standard Deviation price band.
*   **Exit / Trailing Stop:** Sell 50% at $1.5\text{R}$ (where $\text{R}$ is the initial risk distance), move remaining stop to entry, and trail the rest with the daily 9-day EMA.

#### Setup 3: Episodic Pivot (EP / Post-Earnings Announcement Drift - PEAD)
*   **Concept:** A structural breakout on massive volume driven by a major earnings surprise or structural catalyst, marking the start of a multi-week institutional accumulation campaign.
*   **Trigger / Scanner Condition:** Price gaps $>8\%$ out of a consolidation range on historic volume ($\text{PM/ADV Ratio} \ge 5\%$) driven by a Tier 1 catalyst. Entry on a breakout above the daily 50-day resistance pivot.
*   **Stop-Loss:** Low of the EP Day (LOD).
*   **Target:** $+4$ to $+6$ Average True Range (ATR) extension over a multi-week period.
*   **Exit / Trailing Stop:** Sell 40% at $2\text{R}$, sell 30% at $4\text{R}$, and trail the final 30% using the daily 9-day EMA.

#### Setup 4: Red-to-Green (R2G) Intraday Reversal
*   **Concept:** A stock opens below yesterday's close (red) but buying pressure pushes it above yesterday's close, triggering algorithmic buying programs at the cross.
*   **Trigger / Scanner Condition:** Open price is below yesterday's close. Ticker rallies and crosses above yesterday's close on expanding volume ($RVOL_{TS} > 1.5$) with Cumulative Delta trending up.
*   **Stop-Loss:** Low of Day (LOD) at the time of the cross.
*   **Target:** Premarket High (PMH).
*   **Exit / Trailing Stop:** Sell 50% at yesterday's close + $1.5\text{R}$, move stop to breakeven, and trail the remainder to the PMH.

#### Setup 6: Gamma Squeeze / Short Squeeze Sweep
*   **Concept:** Heavily shorted stocks or stocks with high call option demand crossing the GEX Flip level, forcing dealer short covering.
*   **Trigger / Scanner Condition:** Short Interest $>15\%$ or high call option volume anomaly. Price crosses GEX Flip Level into negative gamma with delta velocity spiking ($ROC > 2.0$).
*   **Stop-Loss:** GEX Flip Level - 10 cents.
*   **Target:** $+2$ Standard Deviation price expansion target.
*   **Exit / Trailing Stop:** Sell 40% at $2\text{R}$, sell 30% at $4\text{R}$, and trail the remaining 30% until a reversal bar prints on the 5-minute chart.

#### Setup 7: Day 2/3 Momentum Continuation
*   **Concept:** Institutions spreading large block orders over multiple days following an initial Day 1 Episodic Pivot (EP).
*   **Trigger / Scanner Condition:** Day 1 was a verified EP. Day 2 opens without an excessive gap ($<4\%$ from Day 1 close) and breaks above the Day 1 High on morning volume $>1.5\times$ historical morning average.
*   **Stop-Loss:** Day 2 Low of Day (LOD).
*   **Target:** $+2$ ATR extension of the Day 1 high.
*   **Exit / Trailing Stop:** Sell 50% at $2\text{R}$, move stop to breakeven, and trail the remainder with the daily 9-EMA.

#### Setup 8: High Tight Flag (HTF)
*   **Concept:** Extreme momentum setup. A stock doubles in price in under 30 days and consolidates sideways, showing that institutions refuse to distribute shares.
*   **Trigger / Scanner Condition:** Price gained $\ge 100\%$ in the last 30 trading days. Price consolidates sideways within a tight flag range ($\le 25\%$ depth) for 5 to 15 trading days. Entry on a daily close breaking out above the flag high on volume $>2\times$ average.
*   **Stop-Loss:** Low of the flag consolidation range.
*   **Target:** $+50\%$ extension from the flag breakout point.
*   **Exit / Trailing Stop:** Sell 50% at $3\text{R}$ (swing breakout target), move stop to breakeven, and trail the remaining 50% using the daily 10-EMA.

#### Setup 12: Standard Opening Range Breakout (ORB) (Intraday)
*   **Concept:** Buying a high-relative-volume stock that breaks out above its initial 15-minute high. Unlike Gap and Go, the stock does not need to gap up significantly at the open.
*   **Trigger / Scanner Condition:** Intraday volume spike ($RVOL_{TS} > 1.5$). Plot the high and low of the first 15 minutes of the regular session. Entry triggers when a 5-minute candle closes above the 15-minute high.
*   **Stop-Loss:** Midpoint of the 15-minute range or the 15-minute low (PML/ORL).
*   **Target:** $+2$ Standard Deviation price expansion.
*   **Exit / Trailing Stop:** Sell 50% at $1.5\text{R}$, move stop to breakeven, and trail the remaining 50% with VWAP or the 9 EMA.

#### Setup 13: "Blue Sky" / All-Time High (ATH) Breakout (Swing)
*   **Concept:** Buying a stock breaking out to all-time highs (or multi-year highs). Since there is zero overhead supply (no historical trapped longs selling at breakeven), price can rise rapidly.
*   **Trigger / Scanner Condition:** Price consolidates for $\ge 30$ trading days within 5% of its All-Time High. Entry is triggered when price closes above the ATH on volume $>1.5\times$ 20-day average.
*   **Stop-Loss:** Daily close below the previous breakout pivot level or the daily 10-EMA.
*   **Target:** $+20\%$ to $+30\%$ extension from the ATH level.
*   **Exit / Trailing Stop:** Sell 40% at $2\text{R}$, sell 30% at $4\text{R}$, and trail the remaining 30% with the daily 10-EMA.

#### Setup 14: Stage 1 to Stage 2 Trend Reversal (200 SMA Breakout) (Swing)
*   **Concept:** The macro transition from a long downtrend/consolidation (Stage 1) to a primary uptrend (Stage 2) as institutions accumulate shares.
*   **Trigger / Scanner Condition:** Price has spent $\ge 60$ trading days below the 200-day simple moving average (SMA). Entry triggers when a daily candle closes above the 200 SMA on volume $>2\times$ average. Concurrency: the 50 SMA is sloping upwards or crossing above the 200 SMA (Golden Cross).
*   **Stop-Loss:** Daily close below the 200 SMA by more than 2%.
*   **Target:** $+50\%$ to $+100\%$ macro swing extension.
*   **Exit / Trailing Stop:** Sell 30% at $3\text{R}$, sell 30% at $6\text{R}$, and trail the final 40% using the daily 50 SMA.

#### Setup 15: Post-Earnings Announcement Drift (PEAD) Consolidation Breakout (Swing)
*   **Concept:** Entering a stock that is undergoing post-earnings drift after its initial Day 1 Episodic Pivot (EP). Instead of chasing, the trader buys the breakout of the first multi-week flag/consolidation pattern.
*   **Trigger / Scanner Condition:** The stock had a verified EP within the last 40 trading days. Price consolidates in a tight range (daily flag/channel) above the EP gap low on declining volume. Entry triggers when a daily candle closes above the consolidation resistance on volume $>1.5\times$ average.
*   **Stop-Loss:** Daily close below the consolidation support line.
*   **Target:** $+20\%$ swing extension.
*   **Exit / Trailing Stop:** Sell 50% at $2\text{R}$, move stop to breakeven, and trail the remaining 50% with the daily 21-EMA.

---

### Category B: Anticipation & Volatility Contraction Setups (MOS-A)
*These setups focus on entering before the breakout occurs. They require price volatility to contract and volume to shrink (dry up), signaling the complete exhaustion of selling pressure. High volume or high volatility during consolidation is a negative signal.*

#### Setup 9: Volatility Contraction Pattern (VCP) & Cup & Handle Pivot
*   **Concept:** Systematic absorption of overhead supply. As sellers dry up, price waves contract in depth. The breakout above the final tight consolidation pivot (the "cheat" or "handle") launches the next leg.
*   **Trigger / Scanner Condition:** Stock in Stage 2 uptrend ($Price > 150 > 200$ EMA). Price exhibits 2 to 4 distinct contractions in price volatility (e.g., $20\% \rightarrow 10\% \rightarrow 4\%$). Volume dries up to $<50\%$ of ADV on the final contraction. Entry is triggered when price crosses the contraction pivot (the "cheat") on volume expansion $>2\times$ average.
*   **Stop-Loss:** Low of the last contraction wave (the handle low).
*   **Target:** $+30\%$ extension from the pivot breakout.
*   **Exit / Trailing Stop:** Sell 40% at $2\text{R}$, sell 30% at $4\text{R}$, and trail the final 30% using the daily 21-EMA. Because the entry is extremely tight, these setups frequently yield risk-reward ratios $> 4:1$.

---

### Category C: Mean Reversion & Trend Pullback Setups (MOS-P)
*These setups exploit trend corrections. They require the stock to pull back to major institutional support levels (VWAP, EMA, SMA) on declining volume, followed by a localized volume expansion on the bounce.*

#### Setup 2: Gap and Fade (Intraday Reversal)
*   **Concept:** Shorting (or fading) a stock that gaps up on weak/generic news that fails to hold its opening levels in a Positive Gamma regime.
*   **Trigger / Scanner Condition:** Premarket Gap $>5\%$ but on weak volume ($RVOL_{TS} < 1.0$ and $\text{PM/ADV Ratio} < 1\%$). Price opens near PMH or GEX Call Wall and fails, closing back below PMH on a 1-minute chart with Cumulative Delta flattening and Sonar Pulse Ratio $< 0.15$.
*   **Stop-Loss:** High of Day (HOD) + 5 cents.
*   **Target:** GEX Flip Level or Premarket Low (PML).
*   **Exit / Trailing Stop:** Sell 50% at $1.5\text{R}$, move stop to breakeven, and cover the remaining 50% at the GEX Flip Level.

#### Setup 5: VWAP Institutional Hold & Re-Entry
*   **Concept:** Institutions defend VWAP on high-conviction names. A pullback to VWAP that holds is a low-risk entry.
*   **Trigger / Scanner Condition:** Active stock in a strong daily uptrend pulls back to touch VWAP (within 0.1% buffer). Large limit buy orders stack on the DOM at VWAP, followed by a 1-minute close green away from VWAP.
*   **Stop-Loss:** VWAP - 5 cents.
*   **Target:** High of Day (HOD).
*   **Exit / Trailing Stop:** Sell 50% at $1.5\text{R}$ (or near HOD) and trail the remaining 50% with VWAP as a trailing stop.

#### Setup 10: 10/21 EMA Short-Term Trend Pullback (The Momentum Glide)
*   **Concept:** In a strong Stage 2 uptrend, price rides the 10 EMA or 21 EMA. Pullbacks to these lines represent low-risk add or entry points.
*   **Trigger / Scanner Condition:** Stock in Stage 2 uptrend ($Price > 10\text{ EMA} > 21\text{ EMA} > 200\text{ SMA}$). Price pulls back to touch either the 10 EMA or 21 EMA on declining volume. Entry is triggered when a candle closes green reclaiming/bouncing off the EMA on volume greater than the previous 3 candles.
*   **Stop-Loss:** Daily close below the 21 EMA by more than 1%.
*   **Target:** Prior swing high.
*   **Exit / Trailing Stop:** Sell 50% at the prior swing high (or $1.5\text{R}$), move stop to breakeven, and trail the rest along the 21 EMA.

#### Setup 11: 50 SMA Institutional Support Bounce
*   **Concept:** The 50-day simple moving average is the primary accumulation floor for institutional support.
*   **Trigger / Scanner Condition:** Stock in Stage 2 uptrend ($Price > 50\text{ SMA} > 200\text{ SMA}$). Price pulls back to the 50 SMA on declining volume and contracting volatility. Reversal trigger is fired when a daily candle closes green (e.g., hammer or engulfing pattern) at the 50 SMA on volume $>1.5\times$ average.
*   **Stop-Loss:** Daily close below the 50 SMA by more than 1.5% or below the low of the reversal candle.
*   **Target:** Previous major swing high.
*   **Exit / Trailing Stop:** Sell 40% at the previous swing high (anticipating a double-top structure), sell 30% at $+2$ standard deviations, and trail the final 30% along the 50 SMA.

---

## 4. Tailored Setup Scoring Rubrics

Rather than utilizing a flawed universal scoring system, the playbook implements **three distinct, customized rubrics** designed for the structural requirements of each setup category.

---

### Rubric 1: Breakout & Momentum Shock Scorecard (MOS-B)
*This scorecard rewards explosive news catalysts, vertical volume expansion ($RVOL$), and aggressive order execution.*

| Category | Factor Checked | Condition | Score |
| :--- | :--- | :--- | :--- |
| **1. Catalyst** | Quality & Recency | **Tier 1:** Earnings blowout, FDA approval, or auditor change.<br>**Tier 2:** Analyst upgrade, sector momentum, general news.<br>**Tier 3:** Technical gap only, stale news (>24h), or "No catalyst" found. | **+3.0 pts**<br>**+1.0 pt**<br>**+0.0 pts** |
| **2. Volume** | Relative Strength | **Historic:** $RVOL_{TS} > 3.0$ AND $\text{PM/ADV Ratio} \ge 5\%$.<br>**Standard:** $RVOL_{TS} \ge 1.5$ OR $\text{PM/ADV Ratio} \ge 2\%$.<br>**Weak:** $RVOL_{TS} < 1.0$ AND $\text{PM/ADV Ratio} < 1\%$. | **+2.5 pts**<br>**+1.5 pts**<br>**-1.0 pt** |
| **3. Vol Regime** | Option GEX Profile | **Negative Gamma:** Price is below GEX Flip Level (volatility expansions).<br>**Positive Gamma:** Price is above GEX Flip Level (volatility dampening). | **+1.5 pts**<br>**-1.0 pt** |
| **4. Order Flow** | Cumulative Delta | **Sweep:** Cumulative Delta trending sharply with price; Ask liquidity pulling.<br>**Flat/Reversal:** Delta flattens or is in divergence against price breakout. | **+1.0 pt**<br>**-1.0 pt** |
| **5. Technicals** | Key Levels | **Breakout:** Price closes above Premarket High (PMH) & GEX Flip.<br>**Range-Bound:** Price is trapped inside PMH-PML range.<br>**Breakdown:** Price breaks below Premarket Low (PML). | **+2.0 pts**<br>**+0.0 pts**<br>**-2.0 pts** |

---

### Rubric 2: Anticipation & Volatility Contraction Scorecard (MOS-A)
*This scorecard rewards price tighteness, Stage 2 trend alignment, and **volume dry-up** (low volume). High volume during consolidation is penalized.*

| Category | Factor Checked | Condition | Score |
| :--- | :--- | :--- | :--- |
| **1. Trend Alignment**| Stage 2 Primary Trend| **Uptrend:** Price $> 150 > 200$ EMA, both EMAs sloping upward.<br>**Stage 1 Consolidation:** Price flat, EMAs crossing.<br>**Stage 4 Downtrend:** Price $< 150 < 200$ EMA. | **+3.0 pts**<br>**+1.0 pt**<br>**-3.0 pts** |
| **2. Contraction** | Wave Wave Count & Depth| **Tighter waves:** 3-4 distinct contractions in price volatility.<br>**Standard:** 2 contractions.<br>**No Contraction:** Price is erratic or flat. | **+3.0 pts**<br>**+1.5 pts**<br>**+0.0 pts** |
| **3. Volume Dry-Up** | Supply Exhaustion | **Dry-up:** Final contraction wave volume $<50\%$ of 30-day ADV.<br>**Moderate:** Volume is $50\% - 100\%$ of ADV.<br>**High Volume:** Volume is $>100\%$ of ADV (indicates distribution). | **+2.5 pts**<br>**+1.0 pt**<br>**-1.5 pts** |
| **4. GEX Support** | Option Key Levels | **Aligned:** Pivot point aligned with GEX Flip level or major Put Wall.<br>**Not Aligned:** Pivot sits in thin liquidity zones. | **+1.5 pts**<br>**+0.0 pts** |

---

### Rubric 3: Pullback & Reversion Scorecard (MOS-P)
*This scorecard rewards moving average support, volume drying up on the pullback, and localized volume expanding on the reversal candle.*

| Category | Factor Checked | Condition | Score |
| :--- | :--- | :--- | :--- |
| **1. Trend Strength** | Moving Average Stack | **Bullish Stack:** $Price > EMA10 > EMA21 > SMA50 > SMA200$.<br>**Flat Stack:** Price crossing moving averages, averages are flat.<br>**Bearish Stack:** $Price < EMA10 < EMA21 < SMA50 < SMA200$. | **+3.0 pts**<br>**+1.0 pt**<br>**-3.0 pts** |
| **2. Pullback Volume** | Distribution Check | **Dry-up:** Volume shrinks during pullback ($Vol < 60\%$ of 30-day ADV).<br>**Heavy Vol:** Volume remains high on pullback (heavy distribution). | **+2.5 pts**<br>**-1.5 pts** |
| **3. Reversal Trigger**| Candlestick Rejection | **Bullish Candle:** Green engulfing, hammer, or pinbar close on Daily/5m.<br>**Weak Candle:** Doji, spin top, or red close. | **+3.0 pts**<br>**+0.0 pts** |
| **4. Support Zones** | Key Level Confluence | **Confluence:** Bounce occurs exactly at 10/21 EMA, 50 SMA, or Put Wall.<br>**No Confluence:** Bounce occurs in mid-air. | **+1.5 pts**<br>**+0.0 pts** |

---

## 5. Risk Management & Execution Matrix

Position sizing and risk allocation are dynamically determined by the score calculated from the respective setup's rubric:

### A. Position Sizing & Capital Allocation

| MOS Score | Conviction Level | Risk per Trade (R) | Equity Allocation |
| :--- | :--- | :--- | :--- |
| **9.0 - 10.0** | High-Conviction (Tier 1) | **2.0%** of account equity | **100%** of standard unit size |
| **7.0 - 8.5** | Moderate (Tier 2) | **1.0%** of account equity | **50%** of standard unit size |
| **5.0 - 6.5** | Low-Conviction / Tactical (Tier 3) | **0.5%** of account equity | **25%** of standard unit size |
| **< 5.0** | Unfavorable | **0.0%** | **No Entry** (or Short Fade only) |

### B. Execution Rules
1.  **Stop-Loss Discipline:** Stop-losses are hard-coded on entry. No manual adjustment of stops lower is permitted.
2.  **Breakeven Adjustments:** For all breakout plays (MOS-B) and VCP breakouts (MOS-A), once Partial Take-Profit 1 (PTP 1) is achieved, the stop-loss of the remaining position **must be moved to the entry price (breakeven)**.
3.  **Slippage Penalty:** If execution slippage exceeds 0.5% of the entry price, size down by 50% for subsequent entries on that ticker to protect risk parameters.
