import numpy as np
import pandas as pd
from typing import Dict, Tuple

def find_gex_key_levels(options_df: pd.DataFrame) -> Dict[str, float]:
    """
    Identifies options GEX Call Wall, Put Wall, and Flip level from options data.
    
    Expected options_df columns:
        - strike: float (Option Strike Price)
        - type: str ('call' or 'put')
        - open_interest: float (Option Open Interest)
        - gamma: float (Option Gamma)
        
    Returns:
        Dict containing call_wall, put_wall, and gex_flip_level.
    """
    if options_df.empty:
        return {"call_wall": 0.0, "put_wall": 0.0, "gex_flip": 0.0}
        
    # Calculate GEX for each option strike
    # Standard assumption: MM short puts (negative GEX) and long calls (positive GEX)
    options_df['gex'] = options_df.apply(
        lambda row: row['open_interest'] * row['gamma'] * 100 if row['type'] == 'call'
        else -row['open_interest'] * row['gamma'] * 100,
        axis=1
    )
    
    # Call Wall: strike with maximum positive GEX
    calls = options_df[options_df['type'] == 'call']
    call_wall = float(calls.loc[calls['gex'].idxmax()]['strike']) if not calls.empty else 0.0
    
    # Put Wall: strike with maximum negative GEX (minimum value)
    puts = options_df[options_df['type'] == 'put']
    put_wall = float(puts.loc[puts['gex'].idxmin()]['strike']) if not puts.empty else 0.0
    
    # GEX Flip level: strike where cumulative GEX crosses from positive to negative
    # Group GEX by strike
    grouped = options_df.groupby('strike')['gex'].sum().sort_index()
    
    # Locate zero crossover
    gex_flip = 0.0
    strikes = grouped.index.values
    gex_values = grouped.values
    
    for i in range(len(gex_values) - 1):
        if (gex_values[i] < 0 and gex_values[i+1] > 0) or (gex_values[i] > 0 and gex_values[i+1] < 0):
            # Linear interpolation for flip level estimation
            s1, s2 = strikes[i], strikes[i+1]
            g1, g2 = gex_values[i], gex_values[i+1]
            gex_flip = float(s1 - g1 * (s2 - s1) / (g2 - g1))
            break
            
    # Default to midpoint between walls if no clear crossover found
    if gex_flip == 0.0:
        gex_flip = (call_wall + put_wall) / 2.0
        
    return {
        "call_wall": call_wall,
        "put_wall": put_wall,
        "gex_flip": gex_flip
    }


def get_gamma_regime(spot_price: float, gex_flip: float) -> str:
    """
    Determines if spot price is in a positive or negative gamma regime.
    
    - Positive Gamma (Above Flip): Volatility is suppressed, favoring mean-reversions.
    - Negative Gamma (Below Flip): Volatility is accelerated, favoring breakouts.
    """
    if spot_price >= gex_flip:
        return "Positive Gamma"
    return "Negative Gamma"
