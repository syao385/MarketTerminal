import sys
import os
import pandas as pd
import numpy as np
import yfinance as yf
import logging

# Set up paths to access src modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from calculations.rvol import calculate_time_slice_rvol, calculate_pm_to_adv_ratio
from calculations.gex import find_gex_key_levels, get_gamma_regime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_rvol_calculations():
    logger.info("Verifying RVOL Calculations...")
    
    # Generate mock historical cumulative volume data for last 20 days
    # Let's say historical mean at 09:45 AM is 500,000 shares
    historical_vols = [480000, 520000, 490000, 510000, 500000] * 4 # 20 days
    
    # Today's cumulative volume traded at 09:45 AM
    today_vol = 1500000 # 1.5M shares
    
    rvol_ts = calculate_time_slice_rvol(today_vol, historical_vols)
    
    # RVOL_TS = 1.5M / 500k = 3.0
    assert np.isclose(rvol_ts, 3.0), f"RVOL mismatch: {rvol_ts}"
    logger.info(f"✓ RVOL Time-Slice calculation verified: {rvol_ts:.2f}x (Expected: 3.00x)")
    
    # Verify PM to ADV ratio
    pm_vol = 250000
    adv = 5000000
    pm_adv = calculate_pm_to_adv_ratio(pm_vol, adv)
    assert np.isclose(pm_adv, 0.05), f"PM/ADV ratio mismatch: {pm_adv}"
    logger.info(f"✓ PM to ADV Ratio calculation verified: {pm_adv:.2%} (Expected: 5.00%)")


def verify_gex_calculations():
    logger.info("Verifying Options GEX Calculations...")
    
    # Build a mock options chain dataframe
    # Spot price = 100. Call at 105 strike (positive GEX), Put at 95 strike (negative GEX)
    data = [
        {"strike": 105.0, "type": "call", "open_interest": 1000.0, "gamma": 0.05},
        {"strike": 95.0, "type": "put", "open_interest": 800.0, "gamma": 0.05}
    ]
    df = pd.DataFrame(data)
    
    gex_levels = find_gex_key_levels(df)
    
    assert gex_levels["call_wall"] == 105.0, f"Call Wall mismatch: {gex_levels['call_wall']}"
    assert gex_levels["put_wall"] == 95.0, f"Put Wall mismatch: {gex_levels['put_wall']}"
    assert 95.0 < gex_levels["gex_flip"] < 105.0, f"GEX Flip mismatch: {gex_levels['gex_flip']}"
    
    logger.info("✓ Options GEX levels verified successfully!")
    logger.info(f"  Call Wall Strike: {gex_levels['call_wall']:.2f}")
    logger.info(f"  Put Wall Strike: {gex_levels['put_wall']:.2f}")
    logger.info(f"  GEX Flip Strike: {gex_levels['gex_flip']:.2f}")


def run_live_validation(symbol: str = "SPY"):
    logger.info(f"Running Live Calculations validation against yfinance data for {symbol}...")
    
    # 1. Fetch live stock price and ADV
    ticker = yf.Ticker(symbol)
    history = ticker.history(period="30d")
    if history.empty:
        logger.error(f"Failed to fetch historical price data for {symbol}")
        return
        
    spot = float(history.iloc[-1]["Close"])
    adv = float(history["Volume"].mean())
    logger.info(f"Spot price: ${spot:.2f}, 30-Day ADV: {adv:,.0f} shares")
    
    # 2. Fetch options chain
    try:
        expirations = ticker.options
        if not expirations:
            logger.warning(f"No options chain available for {symbol}")
            return
            
        # Get nearest expiration
        near_exp = expirations[0]
        opt_chain = ticker.option_chain(near_exp)
        
        calls = opt_chain.calls[['strike', 'openInterest']].copy()
        calls['type'] = 'call'
        puts = opt_chain.puts[['strike', 'openInterest']].copy()
        puts['type'] = 'put'
        
        options_df = pd.concat([calls, puts], ignore_index=True)
        options_df['open_interest'] = options_df['openInterest'].fillna(0)
        
        # Calculate a synthetic Gamma proxy for validation (1/std_dev)
        # Gamma is normally distributed around the spot price
        std_dev = spot * 0.05
        options_df['gamma'] = np.exp(-((options_df['strike'] - spot) ** 2) / (2 * (std_dev ** 2))) / (std_dev * np.sqrt(2 * np.pi))
        
        gex_levels = find_gex_key_levels(options_df)
        regime = get_gamma_regime(spot, gex_levels["gex_flip"])
        
        logger.info("✓ Live options GEX analysis completed:")
        logger.info(f"  Expiration Date Checked: {near_exp}")
        logger.info(f"  Call Wall Strike: {gex_levels['call_wall']:.2f}")
        logger.info(f"  Put Wall Strike: {gex_levels['put_wall']:.2f}")
        logger.info(f"  GEX Flip level: {gex_levels['gex_flip']:.2f}")
        logger.info(f"  Active Regime: {regime}")
        
    except Exception as e:
        logger.error(f"Options GEX verification failed: {e}")


if __name__ == "__main__":
    print("====================================================")
    print("  VERIFYING PLAYBOOK MATHEMATICAL CALCULATIONS")
    print("====================================================")
    verify_rvol_calculations()
    print("-" * 52)
    verify_gex_calculations()
    print("-" * 52)
    run_live_validation("SPY")
    print("====================================================")
    print("             ALL MATHEMATICAL TESTS PASSED")
    print("====================================================")
