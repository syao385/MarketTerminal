import uvicorn
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import yfinance as yf
import numpy as np
import pandas as pd
import logging

from calculations.rvol import calculate_time_slice_rvol, calculate_pm_to_adv_ratio
from calculations.gex import find_gex_key_levels, get_gamma_regime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AetherServer")

app = FastAPI(title="Aether Momentum Algo-Engine Server")

# Enable CORS so the browser terminal can access the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/indicators")
def get_indicators(symbol: str = Query(..., description="Stock symbol (e.g. SPY, SMCI)")):
    """
    Computes GEX and RVOL parameters for the requested symbol.
    """
    logger.info(f"Computing indicators for {symbol}...")
    symbol = symbol.upper().strip()
    
    try:
        ticker = yf.Ticker(symbol)
        history = ticker.history(period="30d")
        if history.empty:
            return {"success": False, "error": f"No price history found for {symbol}"}
            
        spot = float(history.iloc[-1]["Close"])
        adv = float(history["Volume"].mean())
        
        # 1. Option GEX calculations
        gex_data = {"call_wall": 0.0, "put_wall": 0.0, "gex_flip": 0.0, "regime": "Unknown"}
        expirations = ticker.options
        if expirations:
            # Check nearest expiration (0DTE/1DTE)
            near_exp = expirations[0]
            opt_chain = ticker.option_chain(near_exp)
            
            calls = opt_chain.calls[['strike', 'openInterest']].copy()
            calls['type'] = 'call'
            puts = opt_chain.puts[['strike', 'openInterest']].copy()
            puts['type'] = 'put'
            
            options_df = pd.concat([calls, puts], ignore_index=True)
            options_df['open_interest'] = options_df['openInterest'].fillna(0)
            
            # Calculate a synthetic Gamma profile (normally distributed around spot price)
            std_dev = spot * 0.05
            options_df['gamma'] = np.exp(-((options_df['strike'] - spot) ** 2) / (2 * (std_dev ** 2))) / (std_dev * np.sqrt(2 * np.pi))
            
            gex_levels = find_gex_key_levels(options_df)
            gex_levels["regime"] = get_gamma_regime(spot, gex_levels["gex_flip"])
            gex_data = gex_levels

        # 2. RVOL calculations
        # Intraday 15-minute intervals for regular hours time-slice RVOL
        # For validation, we use a rolling standard deviation proxy or download recent history
        hist_1d = ticker.history(period="2d", interval="15m")
        rvol_ts = 1.0
        rvol_rm = 1.0
        
        if not hist_1d.empty and len(hist_1d) >= 2:
            # Cumulative volumes
            today_cumulative = float(hist_1d["Volume"].iloc[-1])
            yesterday_cumulative = float(hist_1d["Volume"].iloc[0]) # Proxy historical slice
            rvol_ts = float(today_cumulative / (yesterday_cumulative if yesterday_cumulative > 0 else 1.0))
            rvol_rm = rvol_ts # Simplified proxy for validation feed
            
        return {
            "success": True,
            "symbol": symbol,
            "spot": spot,
            "gex": gex_data,
            "rvol": {
                "rvol_ts": rvol_ts,
                "rvol_rm": rvol_rm,
                "pm_adv": 0.02 # Placeholder
            }
        }
        
    except Exception as e:
        logger.error(f"Error compiling indicators for {symbol}: {e}")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
