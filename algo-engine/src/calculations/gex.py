import numpy as np
import pandas as pd
from typing import Dict, Tuple

def find_gex_key_levels(options_df: pd.DataFrame, spot_price: float = 0.0) -> Dict[str, float]:
    """
    Identifies options GEX Call Wall, Put Wall, and Flip level from options data.
    
    Adopts GammaGexTrading engine logic:
        - Filters strikes by spot price proximity (0.6 * spot <= strike <= 1.4 * spot)
        - Falls back to volume if total open interest is zero / illiquid (< 100)
        - Provides realistic spot-relative fallback walls if options data is sparse
    """
    if spot_price <= 0.0 and not options_df.empty and 'strike' in options_df.columns:
        spot_price = float(options_df['strike'].median())

    if spot_price <= 0.0:
        return {"call_wall": 0.0, "put_wall": 0.0, "gex_flip": 0.0}

    # Default fallback walls (5% above/below spot)
    default_call_wall = round(spot_price * 1.05, 2)
    default_put_wall = round(spot_price * 0.95, 2)
    default_flip = round(spot_price, 2)

    if options_df.empty:
        return {"call_wall": default_call_wall, "put_wall": default_put_wall, "gex_flip": default_flip}

    df = options_df.copy()

    # 1. Ensure required numeric columns exist
    if 'openInterest' in df.columns:
        df['openInterest'] = df['openInterest'].fillna(0).astype(float)
    else:
        df['openInterest'] = 0.0

    if 'volume' in df.columns:
        df['volume'] = df['volume'].fillna(0).astype(float)
    else:
        df['volume'] = 0.0

    # 2. Check total Open Interest; if < 100, fallback to volume as proxy for GEX
    total_oi = df['openInterest'].sum()
    if total_oi < 100:
        total_vol = df['volume'].sum()
        if total_vol > 0:
            df['openInterest'] = df['volume']

    # 3. Apply strike proximity filter (+/- 40% of spot price)
    proximity_mask = (df['strike'] >= spot_price * 0.6) & (df['strike'] <= spot_price * 1.4)
    df_near = df[proximity_mask].copy()

    if df_near.empty:
        df_near = df.copy()

    # 4. Compute Gamma and GEX per strike
    if 'gamma' not in df_near.columns or df_near['gamma'].sum() == 0:
        std_dev = max(spot_price * 0.05, 0.5)
        df_near['gamma'] = np.exp(-((df_near['strike'] - spot_price) ** 2) / (2 * (std_dev ** 2))) / (std_dev * np.sqrt(2 * np.pi))

    df_near['gex'] = df_near.apply(
        lambda row: row['openInterest'] * row['gamma'] * 100 if row['type'] == 'call'
        else -row['openInterest'] * row['gamma'] * 100,
        axis=1
    )

    calls = df_near[df_near['type'] == 'call']
    puts = df_near[df_near['type'] == 'put']

    # Call Wall: strike with maximum positive GEX (or highest call OI near spot)
    call_wall = default_call_wall
    if not calls.empty and calls['gex'].max() > 0:
        call_wall = float(calls.loc[calls['gex'].idxmax()]['strike'])
    elif not calls.empty and calls['openInterest'].max() > 0:
        call_wall = float(calls.loc[calls['openInterest'].idxmax()]['strike'])

    # Put Wall: strike with maximum negative GEX (or highest put OI near spot)
    put_wall = default_put_wall
    if not puts.empty and puts['gex'].min() < 0:
        put_wall = float(puts.loc[puts['gex'].idxmin()]['strike'])
    elif not puts.empty and puts['openInterest'].max() > 0:
        put_wall = float(puts.loc[puts['openInterest'].idxmax()]['strike'])

    # GEX Flip level: strike where cumulative GEX crosses zero
    grouped = df_near.groupby('strike')['gex'].sum().sort_index()
    gex_flip = default_flip

    if len(grouped) > 1:
        strikes = grouped.index.values
        gex_values = grouped.values

        for i in range(len(gex_values) - 1):
            if (gex_values[i] < 0 and gex_values[i+1] > 0) or (gex_values[i] > 0 and gex_values[i+1] < 0):
                s1, s2 = strikes[i], strikes[i+1]
                g1, g2 = gex_values[i], gex_values[i+1]
                if g2 != g1:
                    gex_flip = float(s1 - g1 * (s2 - s1) / (g2 - g1))
                break

        if gex_flip == default_flip:
            gex_flip = (call_wall + put_wall) / 2.0

    return {
        "call_wall": round(call_wall, 2),
        "put_wall": round(put_wall, 2),
        "gex_flip": round(gex_flip, 2)
    }

def get_gamma_regime(spot_price: float, gex_flip: float) -> str:
    """
    Determines if spot price is in a positive or negative gamma regime.
    """
    if spot_price >= gex_flip:
        return "Positive Gamma"
    return "Negative Gamma"
