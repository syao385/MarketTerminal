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

### D. Algorithmic Setup 4: Red-to-Green (R2G) Intraday Reversal
```python
# Concept: A stock opens below yesterday's close (red) but buying pressure pushes it green. 
# The crossing point of yesterday's close triggers high-conviction algo & retail buying.
def evaluate_red_to_green(ticker):
    prev_close = get_yesterday_close(ticker)
    open_price = get_today_open(ticker)
    
    if open_price < prev_close:
        monitor_r2g_cross(ticker, prev_close)

def monitor_r2g_cross(ticker, prev_close):
    price = get_live_price(ticker)
    if price > prev_close:
        # Verify aggressive buyers are leading
        if get_cumulative_delta_trend(ticker) == "UP" and get_rvol(ticker) > 1.5:
            entry_price = market_buy(ticker, qty=calculate_standard_qty(ticker))
            stop_loss = get_today_lod(ticker)
            take_profit = get_premarket_high(ticker)
            
            manage_long_trade(ticker, entry_price, stop_loss, take_profit)
```

### E. Algorithmic Setup 5: VWAP Institutional Hold & Re-Entry
```python
# Concept: Institutions execute orders relative to VWAP. In a strong trend, the first pullback 
# to VWAP that holds (indicated by footprint absorption and delta expansion) is a low-risk long entry.
def evaluate_vwap_hold(ticker):
    if is_in_strong_upward_trend(ticker):
        monitor_vwap_pullback(ticker)

def monitor_vwap_pullback(ticker):
    vwap = get_current_vwap(ticker)
    price = get_live_price(ticker)
    
    # Check if price touches VWAP within 0.1%
    if abs(price - vwap) / vwap <= 0.001:
        # Check for passive absorption on DOM (large buy limit blocks stacking)
        if get_resting_bid_depth_at_vwap(ticker) > get_average_bid_depth(ticker) * 2:
            # Wait for first 1-minute close green away from VWAP
            bar = get_candle(ticker, interval="1m", index=0)
            if bar.close > vwap and get_cumulative_delta_trend(ticker) == "UP":
                entry_price = market_buy(ticker, qty=calculate_standard_qty(ticker))
                stop_loss = vwap - 0.05
                take_profit = get_high_of_day(ticker)
                
                manage_long_trade(ticker, entry_price, stop_loss, take_profit)
```

### F. Algorithmic Setup 6: Gamma Squeeze / Short Squeeze Sweep
```python
# Concept: Heavily shorted stocks or stocks with high call option demand crossing the GEX Flip level. 
# Dealer short hedges accelerate, causing rapid vertical price expansion.
def evaluate_gamma_squeeze(ticker):
    short_interest = get_short_interest_percentage(ticker)
    gex_flip = get_gex_flip_level(ticker)
    price = get_live_price(ticker)
    
    # Target heavily shorted stocks crossing GEX Flip into negative gamma
    if (short_interest > 0.15 or has_high_option_volume(ticker)) and price > gex_flip:
        if get_delta_acceleration_rate(ticker) > 2.0: # Delta velocity spike
            # Execute Long Sweep
            entry_price = market_buy(ticker, qty=calculate_squeeze_qty(ticker))
            stop_loss = gex_flip - 0.10
            take_profit = calculate_standard_deviation_target(ticker, std=2)
            
            manage_long_trade(ticker, entry_price, stop_loss, take_profit)
```

## 5. Multi-Day Swing Momentum Setups

These setups focus on intermediate-term (2-to-20 day) holding periods. Institutions trade them because they represent systematic block accumulation over time rather than simple intraday spikes.

### G. Algorithmic Setup 7: Day 2/3 Momentum Continuation
```python
# Concept: Institutions cannot complete large block orders in a single day. 
# A Day 1 Episodic Pivot (EP) is followed by Day 2/3 buying as execution algorithms 
# (VWAP/POV) resume their accumulation programs.
def evaluate_day2_continuation(ticker):
    # Check if yesterday was a Day 1 Episodic Pivot
    if was_episodic_pivot(ticker, days_ago=1):
        day1_high = get_historical_high(ticker, days_ago=1)
        day1_close = get_historical_close(ticker, days_ago=1)
        
        # Monitor for breakout above Day 1 High
        monitor_day2_breakout(ticker, day1_high, day1_close)

def monitor_day2_breakout(ticker, day1_high, day1_close):
    price = get_live_price(ticker)
    
    # Trigger if price breaks above Day 1 High on expanding morning volume
    if price > day1_high and get_morning_volume(ticker) > get_average_morning_volume(ticker) * 1.5:
        # Check that Day 2 did not open with an excessive gap (> 4% from Day 1 Close)
        if (get_today_open(ticker) - day1_close) / day1_close < 0.04:
            entry_price = market_buy(ticker, qty=calculate_swing_qty(ticker))
            stop_loss = get_today_lod(ticker)
            
            # Trail with Daily 9-EMA for multi-day continuation
            manage_swing_trade(ticker, entry_price, stop_loss)
```

### H. Algorithmic Setup 8: High Tight Flag (HTF)
```python
# Concept: Extreme momentum setup (O'Neil/CANSLIM). A stock doubles in price in under 4-8 weeks, 
# then consolidates sideways within a tight range, showing that institutions refuse to sell.
def evaluate_high_tight_flag(ticker):
    # Step 1: Check for 100%+ gain in last 30 trading days
    lowest_30d = get_lowest_price(ticker, period=30)
    highest_30d = get_highest_price(ticker, period=30)
    
    if (highest_30d - lowest_30d) / lowest_30d >= 1.0:
        # Step 2: Verify consolidation depth is <= 25% from the high
        consol_low = get_lowest_price_since(ticker, start_date=get_date_of_high(ticker))
        consol_depth = (highest_30d - consol_low) / highest_30d
        
        if consol_depth <= 0.25:
            # Step 3: Check consolidation duration (5 to 15 days)
            consol_days = get_days_since_high(ticker)
            if 5 <= consol_days <= 15:
                monitor_htf_breakout(ticker, highest_30d)

def monitor_htf_breakout(ticker, breakout_level):
    price = get_live_price(ticker)
    
    # Enter when price breaks above the flag high on volume > 2x 20-day average ADV
    if price > breakout_level and get_projected_daily_volume(ticker) > get_30d_adv(ticker) * 2.0:
        entry_price = market_buy(ticker, qty=calculate_swing_qty(ticker))
        stop_loss = get_htf_consolidation_low(ticker)
        
        # Exit on momentum exhaustion / trend-line break
        manage_swing_trade(ticker, entry_price, stop_loss)
```

### I. Algorithmic Setup 9: Volatility Contraction Pattern (VCP) & Cup and Handle Pivot
```python
# Concept: Developed by Mark Minervini, VCP represents systematic institutional absorption 
# of overhead supply. As sellers dry up, price volatility contracts (tighter waves).
# The breakout above the final contraction (the 'cheat' or pivot) launches the next leg.
def evaluate_vcp_setup(ticker):
    # Step 1: Stock must be in a primary uptrend (Price > 150-day and 200-day EMA)
    if is_in_stage_2_uptrend(ticker):
        # Step 2: Measure contractions (waves) in price history
        waves = calculate_volatility_contractions(ticker) # e.g. [24%, 12%, 5%, 2%]
        
        if len(waves) >= 2 and is_contracting(waves):
            # Step 3: Check for volume dry-up on the final contraction (Volume < 50% of ADV)
            if get_current_wave_volume(ticker) < get_30d_adv(ticker) * 0.5:
                pivot_price = get_vcp_pivot_level(ticker)
                monitor_vcp_breakout(ticker, pivot_price)

def monitor_vcp_breakout(ticker, pivot_price):
    price = get_live_price(ticker)
    
    # Enter when price breaks above pivot line on volume > 2x 20-day average ADV
    if price > pivot_price and get_projected_daily_volume(ticker) > get_30d_adv(ticker) * 2.0:
        entry_price = market_buy(ticker, qty=calculate_swing_qty(ticker))
        stop_loss = get_last_contraction_low(ticker)
        
        manage_swing_trade(ticker, entry_price, stop_loss)
```


