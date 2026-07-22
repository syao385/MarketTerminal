import uvicorn
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import yfinance as yf
import numpy as np
import pandas as pd
import logging

from calculations.rvol import calculate_time_slice_rvol, calculate_pm_to_adv_ratio
from calculations.gex import find_gex_key_levels, get_gamma_regime
from calculations.indicators import calculate_smas, find_unmitigated_gaps, find_unmitigated_fvgs

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AetherServer")

app = FastAPI(title="Aether Momentum Algo-Engine Server")

# Enable CORS
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
    Computes GEX, RVOL, SMAs, unmitigated gaps, and FVGs for the requested symbol.
    """
    logger.info(f"Computing indicators for {symbol}...")
    symbol = symbol.upper().strip()
    
    try:
        ticker = yf.Ticker(symbol)
        
        # Download 250 trading days (approx 1 year) of daily candles for SMA 200 & gaps
        history = ticker.history(period="1y")
        if history.empty:
            return {"success": False, "error": f"No price history found for {symbol}"}
            
        spot = float(history.iloc[-1]["Close"])
        adv = float(history["Volume"].mean())
        
        # Calculate SMAs, Gaps, and FVGs on full daily history
        history = calculate_smas(history)
        unmitigated_gaps = find_unmitigated_gaps(history)
        unmitigated_fvgs = find_unmitigated_fvgs(history)
        
        # 1. Option GEX calculations
        gex_data = {"call_wall": 0.0, "put_wall": 0.0, "gex_flip": 0.0, "regime": "Unknown"}
        expirations = ticker.options
        if expirations:
            near_exp = expirations[0]
            opt_chain = ticker.option_chain(near_exp)
            
            calls = opt_chain.calls[['strike', 'openInterest']].copy()
            calls['type'] = 'call'
            puts = opt_chain.puts[['strike', 'openInterest']].copy()
            puts['type'] = 'put'
            
            options_df = pd.concat([calls, puts], ignore_index=True)
            options_df['open_interest'] = options_df['openInterest'].fillna(0)
            
            std_dev = spot * 0.05
            options_df['gamma'] = np.exp(-((options_df['strike'] - spot) ** 2) / (2 * (std_dev ** 2))) / (std_dev * np.sqrt(2 * np.pi))
            
            gex_levels = find_gex_key_levels(options_df)
            gex_levels["regime"] = get_gamma_regime(spot, gex_levels["gex_flip"])
            gex_data = gex_levels

        # 2. RVOL Calculations (time-slice check against past 2 days intraday)
        hist_1d = ticker.history(period="2d", interval="15m")
        rvol_ts = 1.0
        rvol_rm = 1.0
        if not hist_1d.empty and len(hist_1d) >= 2:
            today_cumulative = float(hist_1d["Volume"].iloc[-1])
            yesterday_cumulative = float(hist_1d["Volume"].iloc[0])
            rvol_ts = float(today_cumulative / (yesterday_cumulative if yesterday_cumulative > 0 else 1.0))
            rvol_rm = rvol_ts
            
        # Format the points dataset to send to frontend (limit to last 60 days to keep chart clean)
        history_subset = history.tail(60)
        points = []
        for date, row in history_subset.iterrows():
            points.append({
                "date": date.strftime('%Y-%m-%d'),
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"]),
                "volume": float(row["Volume"]),
                "sma_20": float(row["sma_20"]) if not pd.isna(row["sma_20"]) else None,
                "sma_50": float(row["sma_50"]) if not pd.isna(row["sma_50"]) else None,
                "sma_200": float(row["sma_200"]) if not pd.isna(row["sma_200"]) else None
            })
            
        # Adjust gap and FVG indices relative to the returned 60-day subset
        # So the frontend can draw them at the correct historical x-axis positions
        start_date_60 = history_subset.index[0]
        visible_gaps = []
        for g in unmitigated_gaps:
            g_date = history.index[g["start_idx"]]
            if g_date >= start_date_60:
                visible_idx = history_subset.index.get_loc(g_date)
                g_copy = g.copy()
                g_copy["start_idx"] = visible_idx
                visible_gaps.append(g_copy)
                
        visible_fvgs = []
        for f in unmitigated_fvgs:
            f_date = history.index[f["start_idx"]]
            if f_date >= start_date_60:
                visible_idx = history_subset.index.get_loc(f_date)
                f_copy = f.copy()
                f_copy["start_idx"] = visible_idx
                visible_fvgs.append(f_copy)

        return {
            "success": True,
            "symbol": symbol,
            "spot": spot,
            "gex": gex_data,
            "rvol": {
                "rvol_ts": rvol_ts,
                "rvol_rm": rvol_rm,
                "pm_adv": float(calculate_pm_to_adv_ratio(adv * 0.05, adv)) # mock ratio
            },
            "points": points,
            "gaps": visible_gaps,
            "fvgs": visible_fvgs
        }
        
    except Exception as e:
        logger.error(f"Error compiling indicators for {symbol}: {e}")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
