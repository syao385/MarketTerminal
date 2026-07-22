# Institutional Momentum & Algorithmic Trading Playbook
## Integrating Option GEX, Cumulative Delta, and Advanced Volume Signature Analysis

This playbook defines the quantitative framework, calculations, and rules for identifying, scoring, and executing high-probability momentum setups (Gap and Go, Gap and Fade, Episodic Pivots). It serves as the functional specification for transitioning the Aether Market Terminal into an automated algorithmic trading system.

---

## 1. Advanced Volume Signature: Institutional Premarket RVOL

In institutional trading, absolute premarket volume (e.g., 300k shares) is secondary to **Relative Volume (RVOL)**. A large-cap stock trading 500k shares in premarket might represent normal liquidity, whereas a mid-cap stock trading 500k shares represents a massive institutional footprint.

### A. The Calculations

Institutions utilize two primary calculations to normalize premarket volume:

#### 1. Time-Slice Relative Volume ($RVOL_{TS}$)
Premarket volume is highly time-dependent (flat at 4:00 AM, surging at 8:00 AM post-earnings, peaking from 9:00 to 9:30 AM). To avoid time-of-day distortion, volume is measured relative to the historical average *at that exact time slice*:

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

## 2. Option GEX & Order Flow Confluence (Ideas from @GammaGexTrading)

By integrating concepts from the neighboring `GammaGexTrading` framework, we overlay options market maker positioning (dealers' hedging constraints) onto the momentum playbook:

### A. Volatility Regimes via GEX Flip
*   **Negative Gamma Regime (Below GEX Flip):** Dealers hedge by selling on price drops and buying on price rises, structurally **accelerating volatility**. Breakout strategies (**Gap & Go**, **Episodic Pivots**) have a much higher success rate in this regime because dealer hedging loops feed the trend.
*   **Positive Gamma Regime (Above GEX Flip):** Dealers hedge by buying on price drops and selling on price rises, **suppressing volatility**. Breakouts are continuously absorbed, making mean reversion strategies (**Gap & Fade**) the dominant setup.

### B. Micro-Order Flow Triggers
*   **Cumulative Delta Trend:** Shows the cumulative difference between market buy and market sell orders:
    $$\text{Cumulative Delta} = \sum (\text{Aggressive Buys} - \text{Aggressive Sells})$$
    A vertical delta line confirms aggressive buyers are taking liquidity, supporting a breakout.
*   **Liquidity Pulling (DOM):** Prior to a breakout, resting limit orders on the bid/ask ladder disappear (pull), signaling that passive sellers are stepping out of the way, creating a "liquidity vacuum" that price sweeps through.
*   **Stacked Imbalances (Footprint):** Three or more consecutive price bars printing diagonal buying imbalances ($\ge 3.5\times$ bid size) confirm aggressive institutional sweeps.

---

## 3. Revised Momentum Opportunity Scorecard (MOS)

This institutional scorecard combines the terminal's quantitative indicators with GEX and order flow metrics.

| Category | Factor | Institutional Metric & Condition | Score |
| :--- | :--- | :--- | :--- |
| **1. Catalyst** | Quality & Recency | **Tier 1:** Game-changing catalyst (Earnings surprise, auditor change, M&A).<br>**Tier 2:** Analyst upgrade, sector momentum, generic news.<br>**Tier 3:** No catalyst, technical gap only, or stale news (>24h), or "No catalyst" found. | **+3 pts**<br>**+1 pt**<br>**+0 pts** |
| **2. Volume** | Relative Strength | **Historic:** $RVOL_{TS} > 3.0$ AND $\text{PM/ADV Ratio} \ge 5\%$.<br>**Standard:** $RVOL_{TS} \ge 1.5$ OR $\text{PM/ADV Ratio} \ge 2\%$.<br>**Weak:** $RVOL_{TS} < 1.0$ AND $\text{PM/ADV Ratio} < 1\%$. | **+2 pts**<br>**+1 pt**<br>**-1 pt** |
| **3. Volatility Regime** | Option GEX Profile | **Negative Gamma:** Price is below GEX Flip Level (volatility expansions).<br>**Positive Gamma:** Price is above GEX Flip Level (volatility dampening). | **+1 pt**<br>**-1 pt** |
| **4. Order Flow** | Cumulative Delta | **Sweep:** Cumulative Delta trending sharply with price; Ask liquidity pulling.<br>**Absorption:** Delta rising but price flat at GEX Wall (exhaustion). | **+1 pt**<br>**-1 pt** |
| **5. Technicals** | Key Levels | **Breakout:** Price closes above Premarket High (PMH) & GEX Flip.<br>**Range-Bound:** Price is trapped inside PMH-PML range.<br>**Breakdown:** Price breaks below Premarket Low (PML). | **+3 pts**<br>**+0 pts**<br>**-3 pts** |

### Algorithmic Action Plan:
*   **Score 8 - 10:** **High-Probability Momentum (Gap & Go / Episodic Pivot).** Full capital allocation.
*   **Score 5 - 7:** **Moderate Momentum Trend.** 50% capital allocation. Wait for opening range breakout.
*   **Score < 5:** **Mean Reversion / Fade Setup (Gap & Fade).** Do not go long. Look to short breakdowns below the 5-minute ORL.

---

## 4. Algorithmic Trading Logic (System Specifications)

To prepare for automation, the playbook defines the execution logic for the three setups in pseudocode:

### A. Algorithmic Setup 1: Gap and Go (Breakout)
```python
# Initialization (Run at 09:25 AM EST)
def evaluate_gap_and_go(ticker):
    score = calculate_mos_score(ticker)
    if score >= 8:
        monitor_breakout_levels(ticker)

# Execution Logic (Run at 09:30 AM EST onward)
def monitor_breakout_levels(ticker):
    pmh = get_premarket_high(ticker)
    pml = get_premarket_low(ticker)
    gex_flip = get_gex_flip_level(ticker)
    
    # Wait for the first 5-minute candle close
    first_5m_bar = get_candle(ticker, interval="5m", index=0)
    
    if first_5m_bar.close > pmh and first_5m_bar.close > gex_flip:
        if get_cumulative_delta_trend(ticker) == "UP" and get_stacked_imbalances(ticker) >= 3:
            # Enter Long Position
            entry_price = market_buy(ticker, qty=calculate_position_size(score))
            stop_loss = first_5m_bar.low # Stop at ORL
            take_profit = get_gex_resistance_wall(ticker)
            
            manage_long_trade(ticker, entry_price, stop_loss, take_profit)
```

### B. Algorithmic Setup 2: Gap and Fade (Fakeout)
```python
# Initialization (Run at 09:25 AM EST)
def evaluate_gap_and_fade(ticker):
    score = calculate_mos_score(ticker)
    if score < 5:
        monitor_fade_levels(ticker)

# Execution Logic (Run at 09:30 AM EST onward)
def monitor_fade_levels(ticker):
    pmh = get_premarket_high(ticker)
    gex_call_wall = get_gex_call_wall(ticker)
    
    # Monitor for failure at key levels
    price = get_live_price(ticker)
    if price >= gex_call_wall or price >= pmh:
        if get_sonar_pulse_ratio(ticker) < 0.15 and get_cumulative_delta_trend(ticker) == "FLAT":
            # Enter Short Position on first 1-minute close back below resistance
            first_1m_bar = get_candle(ticker, interval="1m", index=0)
            if first_1m_bar.close < pmh:
                entry_price = market_short(ticker, qty=calculate_position_size(score))
                stop_loss = max(first_1m_bar.high, gex_call_wall) + 0.05
                take_profit = get_gex_flip_level(ticker)
                
                manage_short_trade(ticker, entry_price, stop_loss, take_profit)
```

### C. Algorithmic Setup 3: Episodic Pivot (Momentum Burst)
```python
# Initialization (Run at 09:25 AM EST)
def evaluate_episodic_pivot(ticker):
    pm_volume = get_premarket_volume(ticker)
    avg_daily_volume = get_30d_adv(ticker)
    pm_adv_ratio = pm_volume / avg_daily_volume
    
    if pm_adv_ratio >= 0.05 and has_tier_1_catalyst(ticker):
        monitor_episodic_pivot(ticker)

# Execution Logic
def monitor_episodic_pivot(ticker):
    resistance_50d = get_50d_resistance_pivot(ticker)
    first_15m_bar = get_candle(ticker, interval="15m", index=0)
    
    if first_15m_bar.close > resistance_50d and first_15m_bar.volume > (avg_daily_volume * 0.1):
        # Enter Long Position on Opening Range Breakout
        entry_price = market_buy(ticker, qty=calculate_position_size(score))
        stop_loss = first_15m_bar.low # Stop at LOD
        
        # Hold position for multiple days; trail with 9-day EMA
        manage_swing_trade(ticker, entry_price, stop_loss)
```
