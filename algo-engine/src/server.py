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
def get_indicators(
    symbol: str = Query(..., description="Stock symbol (e.g. SPY, SMCI)"),
    timeframe: str = Query("1d", description="Timeframe resolution (1d, 1h, 5m, 1m)")
):
    """
    Computes GEX, RVOL, SMAs, unmitigated gaps, and FVGs for the requested symbol and timeframe.
    """
    logger.info(f"Computing indicators for {symbol} on {timeframe} timeframe...")
    symbol = symbol.upper().strip()
    timeframe = timeframe.lower().strip()
    
    # Map timeframe to yfinance period/interval config
    timeframe_map = {
        "1d": {"period": "1y", "interval": "1d", "tail": 60},
        "1h": {"period": "60d", "interval": "1h", "tail": 60},
        "5m": {"period": "5d", "interval": "5m", "tail": 60},
        "1m": {"period": "1d", "interval": "1m", "tail": 100}
    }
    
    tf_conf = timeframe_map.get(timeframe, {"period": "1y", "interval": "1d", "tail": 60})
    
    try:
        ticker = yf.Ticker(symbol)
        
        # Download historical candles
        history = ticker.history(period=tf_conf["period"], interval=tf_conf["interval"])
        if history.empty:
            return {"success": False, "error": f"No price history found for {symbol}"}
            
        spot = float(history.iloc[-1]["Close"])
        
        # Calculate daily Average Daily Volume (always daily for PM/ADV check)
        daily_hist = ticker.history(period="30d")
        adv = float(daily_hist["Volume"].mean()) if not daily_hist.empty else 1.0
        
        # Calculate SMAs, Gaps, FVGs, and Volume SMA
        history = calculate_smas(history)
        history['vol_sma_20'] = history['Volume'].rolling(window=20).mean()
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

        # 2. RVOL Calculations (time-slice check against past 20 days)
        rvol_ts = 1.0
        rvol_rm = 1.0
        try:
            df_15m = ticker.history(period="20d", interval="15m")
            if not df_15m.empty and len(df_15m) > 10:
                df_15m['Date'] = df_15m.index.date
                df_15m['Time'] = df_15m.index.time
                df_15m['Cumulative_Volume'] = df_15m.groupby('Date')['Volume'].cumsum()
                
                latest_bar = df_15m.iloc[-1]
                latest_time = latest_bar['Time']
                today_cumulative = float(latest_bar['Cumulative_Volume'])
                
                historical_at_time = df_15m[df_15m['Time'] == latest_time]
                historical_excluding_today = historical_at_time[historical_at_time['Date'] != latest_bar['Date']]
                
                historical_cumulative_volumes = historical_excluding_today['Cumulative_Volume'].tolist()
                
                rvol_ts = calculate_time_slice_rvol(today_cumulative, historical_cumulative_volumes)
                
                daily_history = ticker.history(period="21d")
                if not daily_history.empty:
                    historical_daily_volumes = daily_history["Volume"].iloc[:-1]
                    adv_20d = float(historical_daily_volumes.mean())
                    if adv_20d > 0:
                        rvol_rm = float(today_cumulative / adv_20d)
        except Exception as rvol_err:
            logger.error(f"Error calculating RVOL: {rvol_err}")
            
        # Format the points dataset to send to frontend
        history_subset = history.tail(tf_conf["tail"])
        points = []
        for date, row in history_subset.iterrows():
            points.append({
                "date": date.strftime('%Y-%m-%d %H:%M') if timeframe != "1d" else date.strftime('%Y-%m-%d'),
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"]),
                "volume": float(row["Volume"]),
                "sma_20": float(row["sma_20"]) if not pd.isna(row["sma_20"]) else None,
                "sma_50": float(row["sma_50"]) if not pd.isna(row["sma_50"]) else None,
                "sma_200": float(row["sma_200"]) if not pd.isna(row["sma_200"]) else None,
                "vol_sma_20": float(row["vol_sma_20"]) if not pd.isna(row["vol_sma_20"]) else None
            })
            
        # Adjust gap and FVG indices relative to the returned subset
        start_date_subset = history_subset.index[0]
        visible_gaps = []
        for g in unmitigated_gaps:
            g_date = history.index[g["start_idx"]]
            if g_date >= start_date_subset:
                visible_idx = history_subset.index.get_loc(g_date)
                g_copy = g.copy()
                g_copy["start_idx"] = visible_idx
                visible_gaps.append(g_copy)
                
        visible_fvgs = []
        for f in unmitigated_fvgs:
            f_date = history.index[f["start_idx"]]
            if f_date >= start_date_subset:
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
                "pm_adv": float(calculate_pm_to_adv_ratio(adv * 0.05, adv))
            },
            "points": points,
            "gaps": visible_gaps,
            "fvgs": visible_fvgs
        }
        
    except Exception as e:
        logger.error(f"Error compiling indicators for {symbol}: {e}")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8080)
