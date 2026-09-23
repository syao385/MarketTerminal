import uvicorn
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yfinance as yf
import numpy as np
import pandas as pd
import logging
import json
import os
import sqlite3
from typing import Optional

from calculations.rvol import calculate_time_slice_rvol, calculate_pm_to_adv_ratio
from calculations.gex import find_gex_key_levels, get_gamma_regime
from calculations.indicators import calculate_smas, find_unmitigated_gaps, find_unmitigated_fvgs
from calculations.backtester import PlaybookBacktester
from calculations.optimizer import SetupParameterOptimizer
from calculations.scanner import PlaybookScanner

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AetherServer")

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "trading_system.db"))

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS journal_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            setup_id TEXT NOT NULL,
            setup_name TEXT NOT NULL,
            score REAL NOT NULL,
            metrics TEXT NOT NULL,
            breakdown TEXT NOT NULL,
            risk_parameters TEXT NOT NULL,
            status TEXT DEFAULT 'pending'
        )
    """)
    conn.commit()
    
    # Run dynamic schema migration to add direction, setups_json, setup_count, confluence_score if not present
    cursor.execute("PRAGMA table_info(journal_entries)")
    columns = [col[1] for col in cursor.fetchall()]
    if "direction" not in columns:
        cursor.execute("ALTER TABLE journal_entries ADD COLUMN direction TEXT DEFAULT 'long'")
    if "setups_json" not in columns:
        cursor.execute("ALTER TABLE journal_entries ADD COLUMN setups_json TEXT DEFAULT '[]'")
    if "setup_count" not in columns:
        cursor.execute("ALTER TABLE journal_entries ADD COLUMN setup_count INTEGER DEFAULT 1")
    if "confluence_score" not in columns:
        cursor.execute("ALTER TABLE journal_entries ADD COLUMN confluence_score REAL DEFAULT 0.0")
    if "timeframe" not in columns:
        cursor.execute("ALTER TABLE journal_entries ADD COLUMN timeframe TEXT DEFAULT '5m'")
    conn.commit()
    conn.close()

import httpx
import time
from fastapi.responses import FileResponse, Response

init_db()

GEX_CACHE = {}

app = FastAPI(title="Aether Momentum Algo-Engine Server")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/ping")
def ping():
    return {"status": "ok", "service": "MarketTerminal Backend"}

@app.get("/")
def serve_index():
    index_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "index.html"))
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "MarketTerminal Backend Engine is running."}

# Centralized yfinance Cache & Proxy Layer to eliminate duplicate API calls
CANDLE_CACHE = {} # (symbol, interval) -> { "time": timestamp, "data": parsed_dict }
CACHE_TTL_SECONDS = 120 # 2 minutes TTL cache for candle and quote data

@app.get("/api/candles")
def get_candles_proxy(
    symbol: str = Query(..., description="Symbol ticker e.g. NVDA, SPY"),
    interval: str = Query("5m", description="Candle interval resolution e.g. 1m, 5m, 15m, 1d")
):
    symbol = symbol.upper().strip()
    interval = interval.lower().strip()
    cache_key = (symbol, interval)
    now = time.time()

    if cache_key in CANDLE_CACHE and (now - CANDLE_CACHE[cache_key]["time"] < CACHE_TTL_SECONDS):
        logger.info(f"Serving cached candles for {symbol} ({interval}) [Age: {int(now - CANDLE_CACHE[cache_key]['time'])}s]")
        return CANDLE_CACHE[cache_key]["data"]

    try:
        ticker = yf.Ticker(symbol)
        period_map = {"1m": "1d", "5m": "5d", "15m": "5d", "1h": "10d", "1d": "1y"}
        period = period_map.get(interval, "5d")

        df = ticker.history(period=period, interval=interval, prepost=True)
        if df.empty:
            return {"success": False, "error": f"No candlestick data returned for {symbol}"}

        prev_close = float(df.iloc[0]['Close'])
        try:
            fast_info = getattr(ticker, 'fast_info', {})
            prev_close = float(fast_info.get('previousClose') or prev_close)
        except Exception:
            pass

        reg_price = float(df.iloc[-1]['Close'])
        day_high = float(df['High'].max())
        day_low = float(df['Low'].min())
        volume = int(df['Volume'].sum())

        points = []
        for index, row in df.iterrows():
            ts_str = index.strftime('%Y-%m-%d %H:%M') if hasattr(index, 'strftime') else str(index)
            points.append({
                "time": ts_str,
                "value": float(row['Close']),
                "open": float(row['Open']),
                "high": float(row['High']),
                "low": float(row['Low']),
                "volume": int(row['Volume'])
            })

        result = {
            "success": True,
            "meta": {
                "symbol": symbol,
                "regularMarketPrice": reg_price,
                "previousClose": prev_close,
                "chartPreviousClose": prev_close,
                "regularMarketDayHigh": day_high,
                "regularMarketDayLow": day_low,
                "regularMarketVolume": volume,
                "longName": f"{symbol} Inc."
            },
            "points": points
        }

        CANDLE_CACHE[cache_key] = {"time": now, "data": result}
        logger.info(f"Populated central CANDLE_CACHE for {symbol} ({interval}) - {len(points)} points.")
        return result
    except Exception as e:
        logger.error(f"Failed to fetch candles for {symbol} ({interval}): {e}")
        return {"success": False, "error": str(e)}

@app.get("/proxy")
async def proxy_url(url: str = Query(...)):
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            return Response(content=resp.content, status_code=resp.status_code, media_type=resp.headers.get("content-type", "application/json"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
        history = ticker.history(period=tf_conf["period"], interval=tf_conf["interval"], prepost=True)
        if history.empty:
            return {"success": False, "error": f"No price history found for {symbol}"}
            
        # Extract true real-time spot price (supporting premarket & extended hours)
        spot = float(history.iloc[-1]["Close"])
        try:
            pm_5m = ticker.history(period="1d", interval="5m", prepost=True)
            if not pm_5m.empty:
                spot = float(pm_5m.iloc[-1]["Close"])
        except Exception:
            pass
        
        # Calculate daily Average Daily Volume (always daily for PM/ADV check)
        daily_hist = ticker.history(period="30d", prepost=True)
        adv = float(daily_hist["Volume"].mean()) if not daily_hist.empty else 1.0
        
        # Calculate SMAs, Gaps, FVGs, and Volume SMA
        history = calculate_smas(history)
        history['vol_sma_20'] = history['Volume'].rolling(window=20).mean()
        unmitigated_gaps = find_unmitigated_gaps(history)
        unmitigated_fvgs = find_unmitigated_fvgs(history)
        
        # 1. Option GEX calculations with 30-minute cache & port 8000 cross-desk reuse
        now_ts = time.time()
        gex_data = None
        if symbol in GEX_CACHE and (now_ts - GEX_CACHE[symbol]["time"] < 1800):
            gex_data = GEX_CACHE[symbol]["data"]
            logger.info(f"Reusing cached GEX data for {symbol} (age: {int(now_ts - GEX_CACHE[symbol]['time'])}s)")

        # Check local GammaGexTrading desk on port 8000 if not in memory cache
        if gex_data is None:
            try:
                res = httpx.get(f"http://127.0.0.1:8000/api/gex/{symbol}", timeout=0.8)
                if res.status_code == 200:
                    g_json = res.json()
                    gex_data = {
                        "call_wall": float(g_json.get("call_wall", spot * 1.05)),
                        "put_wall": float(g_json.get("put_wall", spot * 0.95)),
                        "gex_flip": float(g_json.get("gamma_flip", spot)),
                        "regime": get_gamma_regime(spot, float(g_json.get("gamma_flip", spot)))
                    }
                    GEX_CACHE[symbol] = {"time": now_ts, "data": gex_data}
                    logger.info(f"Cross-reused GEX levels from GammaGexTrading desk (port 8000) for {symbol}")
            except Exception:
                pass

        # If still None, compute directly and store in cache
        if gex_data is None:
            gex_data = {
                "call_wall": round(spot * 1.05, 2),
                "put_wall": round(spot * 0.95, 2),
                "gex_flip": round(spot, 2),
                "regime": "Positive Gamma"
            }
            try:
                expirations = ticker.options
                if expirations:
                    all_calls = []
                    all_puts = []
                    selected_expirations = expirations[:8]
                    for exp_date_str in selected_expirations:
                        try:
                            opt_chain = ticker.option_chain(exp_date_str)
                            if not opt_chain.calls.empty:
                                c = opt_chain.calls.copy()
                                c['type'] = 'call'
                                c['expiration'] = exp_date_str
                                all_calls.append(c)
                            if not opt_chain.puts.empty:
                                p = opt_chain.puts.copy()
                                p['type'] = 'put'
                                p['expiration'] = exp_date_str
                                all_puts.append(p)
                        except Exception as exp_err:
                            logger.warn(f"Error fetching expiration {exp_date_str} for {symbol}: {exp_err}")
                    
                    if all_calls and all_puts:
                        df_calls = pd.concat(all_calls, ignore_index=True)
                        df_puts = pd.concat(all_puts, ignore_index=True)
                        options_df = pd.concat([df_calls, df_puts], ignore_index=True)
                        gex_levels = find_gex_key_levels(options_df, spot_price=spot)
                        gex_levels["regime"] = get_gamma_regime(spot, gex_levels["gex_flip"])
                        gex_data = gex_levels
            except Exception as e:
                logger.warn(f"Options fetch error for {symbol}: {e}")
            
            GEX_CACHE[symbol] = {"time": now_ts, "data": gex_data}

        # 2. RVOL Calculations (time-slice check against past 20 days)
        rvol_ts = 1.0
        rvol_rm = 1.0
        try:
            df_15m = ticker.history(period="20d", interval="15m", prepost=True)
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
                
                daily_history = ticker.history(period="21d", prepost=True)
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


@app.get("/api/backtest")
def get_backtest(
    symbol: str = Query(..., description="Ticker symbol (e.g. SPY, NVDA)"),
    setup_id: str = Query(..., description="Playbook setup ID (e.g. setup_12, setup_13)"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    capital: float = Query(100000.0, description="Initial starting capital")
):
    """
    Executes a historical backtest of the specified setup.
    """
    logger.info(f"API: Running backtest for {symbol} - {setup_id}...")
    backtester = PlaybookBacktester()
    res = backtester.run_backtest(
        symbol=symbol,
        setup_id=setup_id,
        start_date=start_date,
        end_date=end_date,
        initial_capital=capital
    )
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error", "Backtest failed."))
    return res


@app.get("/api/optimize")
def get_optimization(
    symbol: str = Query(..., description="Ticker symbol"),
    setup_id: str = Query(..., description="Playbook setup ID"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """
    Executes a grid sweep parameter optimization for a setup.
    """
    logger.info(f"API: Optimizing parameters for {symbol} - {setup_id}...")
    optimizer = SetupParameterOptimizer()
    res = optimizer.optimize_setup_parameters(
        symbol=symbol,
        setup_id=setup_id,
        start_date=start_date,
        end_date=end_date
    )
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error", "Optimization failed."))
    return res
@app.get("/api/metrics")
def get_symbol_metrics(symbol: str):
    """
    Computes real-time technical indicators, scorecard, and risk management parameters for any symbol on the fly.
    """
    try:
        symbol = symbol.strip().upper()
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="260d", interval="1d", prepost=True)
        if df.empty or len(df) < 200:
            return {"success": False, "error": "Insufficient history"}
            
        df = calculate_smas(df)
        df['vol_sma_20'] = df['Volume'].rolling(window=20).mean()
        df['rvol'] = df['Volume'] / df['vol_sma_20']
        df['ema_10'] = df['Close'].ewm(span=10, adjust=False).mean()
        df['ema_21'] = df['Close'].ewm(span=21, adjust=False).mean()
        df = df.dropna().copy()
        
        if df.empty:
            return {"success": False, "error": "No valid data points"}
            
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        close = float(latest['Close'])
        open_p = float(latest['Open'])
        high = float(latest['High'])
        low = float(latest['Low'])
        rvol = float(latest['rvol'])
        gap_pct = (open_p - float(prev['Close'])) / float(prev['Close'])
        
        # Sizing and conviction calculation
        from calculations.scorecards import calculate_mos_b, get_risk_allocation
        score = calculate_mos_b(2, rvol, gap_pct, True, True, True)
        
        breakdown = {
            "catalyst": min(3.0, max(0.5, abs(gap_pct) * 50.0)),
            "volume": min(3.0, max(0.5, rvol)),
            "vol_regime": 1.5 if rvol > 1.2 else 0.8,
            "order_flow": 2.0 if close > open_p else 0.5,
            "technicals": min(3.0, max(0.5, (close / float(latest['sma_20']) - 1.0) * 10.0 + 1.5))
        }
        
        total_score = min(10.0, max(0.0, sum(breakdown.values())))
        risk_alloc = get_risk_allocation(total_score)
        
        stop_dist = close * 0.015
        bar_body = abs(close - open_p)
        atr_approx = float((df['High'] - df['Low']).tail(14).mean())
        is_accelerating = (rvol >= 2.0) or (bar_body > 1.2 * atr_approx)
        adaptive_trailing_ema = "10EMA" if is_accelerating else "21EMA"

        return {
            "success": True,
            "symbol": symbol,
            "score": total_score,
            "conviction": risk_alloc["conviction"],
            "risk_pct": risk_alloc["risk_pct"] * 100,
            "is_accelerating": is_accelerating,
            "adaptive_trailing_ema": adaptive_trailing_ema,
            "metrics": {
                "price": close,
                "open": open_p,
                "high": high,
                "low": low,
                "rvol": rvol,
                "gap_pct": gap_pct * 100,
                "sma_20": float(latest['sma_20']),
                "sma_50": float(latest['sma_50']),
                "sma_200": float(latest['sma_200']),
                "ema_10": float(latest['ema_10']),
                "ema_21": float(latest['ema_21']),
                "is_accelerating": is_accelerating,
                "adaptive_trailing_ema": adaptive_trailing_ema
            },
            "score_breakdown": breakdown,
            "risk_parameters": {
                "entry": close,
                "stop": close - stop_dist,
                "target1": close + stop_dist * 1.5,
                "target2": close + stop_dist * 3.0,
                "risk_pct": risk_alloc["risk_pct"] * 100,
                "risk_dollars": 1000.0,
                "size_shares": 100,
            }
        }
    except Exception as e:
        logger.error(f"Error computing scorecard metrics for {symbol}: {e}")
        return {"success": False, "error": str(e)}


@app.get("/api/scanner")
def get_scanner_results(symbols: Optional[str] = Query(None)):
    """
    Scans the watchlist for all 15 playbook setups and returns active triggers.
    """
    logger.info(f"API: Executing watchlist scan for: {symbols or 'default watchlist'}...")
    watchlist = None
    if symbols:
        watchlist = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    scanner = PlaybookScanner(watchlist=watchlist)
    try:
        res = scanner.scan_all_setups()
        return {"success": True, "scans": res}
    except Exception as e:
        logger.error(f"Scanner execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class JournalEntry(BaseModel):
    symbol: str
    timestamp: str
    setup_id: str
    setup_name: str
    score: float
    metrics: dict
    breakdown: dict
    risk_parameters: dict
    status: Optional[str] = "pending"
    direction: Optional[str] = "long"
    setups_json: Optional[list] = []
    setup_count: Optional[int] = 1
    setups_json: Optional[list] = []
    setup_count: Optional[int] = 1
    confluence_score: Optional[float] = 0.0
    timeframe: Optional[str] = "5m"

@app.post("/api/journal")
def save_journal_entry(entry: JournalEntry):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Enforce integer share size in risk parameters (strictly no partial shares)
        if "size_shares" in entry.risk_parameters:
            entry.risk_parameters["size_shares"] = int(entry.risk_parameters["size_shares"])

        setups_str = json.dumps(entry.setups_json) if entry.setups_json else json.dumps([{"setup_id": entry.setup_id, "setup_name": entry.setup_name, "score": entry.score, "direction": entry.direction}])
        count = entry.setup_count or (len(entry.setups_json) if entry.setups_json else 1)
        conf_score = entry.confluence_score or entry.score
        tf = entry.timeframe or "5m"

        cursor.execute("""
            INSERT INTO journal_entries (symbol, timestamp, setup_id, setup_name, score, metrics, breakdown, risk_parameters, status, direction, setups_json, setup_count, confluence_score, timeframe)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            entry.symbol.upper(),
            entry.timestamp,
            entry.setup_id,
            entry.setup_name,
            entry.score,
            json.dumps(entry.metrics),
            json.dumps(entry.breakdown),
            json.dumps(entry.risk_parameters),
            entry.status,
            entry.direction,
            setups_str,
            count,
            conf_score,
            tf
        ))
        last_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return {"success": True, "entry_id": last_id, "message": "Consolidated journal entry saved successfully."}
    except Exception as e:
        logger.error(f"Failed to save journal entry: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/journal")
def get_journal_entries():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, symbol, timestamp, setup_id, setup_name, score, metrics, breakdown, risk_parameters, status, direction, setups_json, setup_count, confluence_score, timeframe FROM journal_entries ORDER BY id DESC")
        rows = cursor.fetchall()
        conn.close()
        
        entries = []
        for r in rows:
            setups_parsed = []
            if len(r) > 11 and r[11]:
                try:
                    setups_parsed = json.loads(r[11])
                except Exception:
                    setups_parsed = []
            
            if not setups_parsed:
                setups_parsed = [{"setup_id": r[3], "setup_name": r[4], "score": r[5], "direction": r[10] if len(r) > 10 else "long"}]

            entries.append({
                "id": r[0],
                "symbol": r[1],
                "timestamp": r[2],
                "setup_id": r[3],
                "setup_name": r[4],
                "score": r[5],
                "metrics": json.loads(r[6]),
                "breakdown": json.loads(r[7]),
                "risk_parameters": json.loads(r[8]),
                "status": r[9],
                "direction": r[10] if len(r) > 10 else "long",
                "setups_json": setups_parsed,
                "setup_count": r[12] if len(r) > 12 and r[12] is not None else len(setups_parsed),
                "confluence_score": r[13] if len(r) > 13 and r[13] is not None else r[5],
                "timeframe": r[14] if len(r) > 14 and r[14] else "5m"
            })
        return {"success": True, "entries": entries}
    except Exception as e:
        logger.error(f"Failed to fetch journal entries: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class JournalStatusUpdate(BaseModel):
    entry_id: int
    status: Optional[str] = None
    risk_parameters: Optional[dict] = None

@app.post("/api/journal/update")
def update_journal_status(update: JournalStatusUpdate):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        if update.status is not None:
            cursor.execute("UPDATE journal_entries SET status = ? WHERE id = ?", (update.status, update.entry_id))
        if update.risk_parameters is not None:
            cursor.execute("UPDATE journal_entries SET risk_parameters = ? WHERE id = ?", (json.dumps(update.risk_parameters), update.entry_id))
        conn.commit()
        conn.close()
        return {"success": True, "message": f"Journal entry {update.entry_id} updated successfully."}
    except Exception as e:
        logger.error(f"Failed to update journal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class AlpacaSettings(BaseModel):
    api_key_id: str
    secret_key: str

@app.get("/api/settings")
def get_settings():
    """
    Reads the user's Alpaca credentials from config/alpaca_config.json.
    """
    config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config", "alpaca_config.json"))
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                config_data = json.load(f)
                return {
                    "success": True,
                    "api_key_id": config_data.get("api_key_id", ""),
                    "secret_key": config_data.get("secret_key", "")
                }
        except Exception as e:
            logger.error(f"Failed to read settings: {e}")
    return {"success": True, "api_key_id": "", "secret_key": ""}

@app.post("/api/settings")
def save_settings(settings: AlpacaSettings):
    """
    Saves the user's Alpaca credentials to config/alpaca_config.json.
    """
    try:
        config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config", "alpaca_config.json"))
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        config_data = {
            "api_key_id": settings.api_key_id.strip(),
            "secret_key": settings.secret_key.strip()
        }
        with open(config_path, "w") as f:
            json.dump(config_data, f, indent=4)
        logger.info("Successfully updated Alpaca settings config on disk.")
        return {"success": True}
    except Exception as e:
        logger.error(f"Failed to save settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8080)
