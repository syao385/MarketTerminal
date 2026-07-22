def calculate_mos_b(
    catalyst_tier: int,
    rvol_ts: float,
    pm_adv: float,
    is_below_flip: bool,
    is_delta_sweep: bool,
    is_technical_breakout: bool
) -> float:
    """
    Rubric 1: Breakout & Momentum Shock Scorecard (MOS-B)
    Max score: 10.0 pts.
    """
    score = 0.0
    
    # 1. Catalyst (Max 3.0)
    if catalyst_tier == 1:
        score += 3.0
    elif catalyst_tier == 2:
        score += 1.0
        
    # 2. Volume (Max 2.5, Min -1.0)
    if rvol_ts > 3.0 and pm_adv >= 0.05:
        score += 2.5
    elif rvol_ts >= 1.5 or pm_adv >= 0.02:
        score += 1.5
    elif rvol_ts < 1.0 and pm_adv < 0.01:
        score -= 1.0
        
    # 3. Vol Regime (Max 1.5, Min -1.0)
    if is_below_flip: # Below flip is Negative Gamma (vol expansion) which breakouts thrive in
        score += 1.5
    else:
        score -= 1.0
        
    # 4. Order Flow (Max 1.0, Min -1.0)
    if is_delta_sweep:
        score += 1.0
    else:
        score -= 1.0
        
    # 5. Technicals (Max 2.0, Min -2.0)
    if is_technical_breakout:
        score += 2.0
    else:
        # Default fallback: range bound
        score += 0.0
        
    # Clamp score between 0.0 and 10.0
    return max(0.0, min(10.0, score))


def calculate_mos_a(
    is_uptrend: bool,
    contractions_count: int,
    final_vol_adv_ratio: float,
    aligned_gex: bool
) -> float:
    """
    Rubric 2: Anticipation & Volatility Contraction Scorecard (MOS-A)
    Max score: 10.0 pts.
    """
    score = 0.0
    
    # 1. Trend Alignment (Max 3.0, Min -3.0)
    if is_uptrend:
        score += 3.0
    else:
        score -= 3.0
        
    # 2. Contraction (Max 3.0)
    if contractions_count >= 3:
        score += 3.0
    elif contractions_count == 2:
        score += 1.5
        
    # 3. Volume Dry-Up (Max 2.5, Min -1.5)
    if final_vol_adv_ratio < 0.50:
        score += 2.5
    elif final_vol_adv_ratio <= 1.0:
        score += 1.0
    else:
        score -= 1.5
        
    # 4. GEX Support (Max 1.5)
    if aligned_gex:
        score += 1.5
        
    return max(0.0, min(10.0, score))


def calculate_mos_p(
    is_bullish_stack: bool,
    pullback_vol_adv_ratio: float,
    is_reversal_candle: bool,
    aligned_support: bool
) -> float:
    """
    Rubric 3: Pullback & Reversion Scorecard (MOS-P)
    Max score: 10.0 pts.
    """
    score = 0.0
    
    # 1. Trend Strength (Max 3.0, Min -3.0)
    if is_bullish_stack:
        score += 3.0
    else:
        score -= 3.0
        
    # 2. Pullback Volume (Max 2.5, Min -1.5)
    if pullback_vol_adv_ratio < 0.60:
        score += 2.5
    else:
        score -= 1.5
        
    # 3. Reversal Trigger (Max 3.0)
    if is_reversal_candle:
        score += 3.0
        
    # 4. Support Zones (Max 1.5)
    if aligned_support:
        score += 1.5
        
    return max(0.0, min(10.0, score))


def get_risk_allocation(mos_score: float) -> dict:
    """
    Decides conviction tier, risk-per-trade (R), and equity allocation based on MOS score.
    Section 5.A of the playbook.
    """
    if mos_score >= 9.0:
        return {"conviction": "Tier 1 (High-Conviction)", "risk_pct": 0.02, "allocation_pct": 1.00}
    elif mos_score >= 7.0:
        return {"conviction": "Tier 2 (Moderate)", "risk_pct": 0.01, "allocation_pct": 0.50}
    elif mos_score >= 5.0:
        return {"conviction": "Tier 3 (Tactical)", "risk_pct": 0.005, "allocation_pct": 0.25}
    else:
        return {"conviction": "No Trade / Filtered", "risk_pct": 0.00, "allocation_pct": 0.00}
