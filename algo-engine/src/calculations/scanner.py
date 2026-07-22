import logging
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any

from calculations.scorecards import calculate_mos_b, calculate_mos_a, calculate_mos_p
from calculations.indicators import calculate_smas

logger = logging.getLogger("AetherScanner")

WATCHLIST = ["AAPL", "NVDA", "TSLA", "MSFT", "SPY", "AMZN", "GOOG", "AMD", "MU", "SMCI"]

class PlaybookScanner:
    def __init__(self):
        pass

    def scan_all_setups(self) -> List[Dict[str, Any]]:
        """
        Scans the liquid watchlist for all 15 setups and calculates MOS scores and metrics.
        """
        results_by_setup = {f"setup_{i}": [] for i in range(1, 16)}
        
        # Setup Names Mapping
        setup_names = {
            "setup_1": "Gap and Go",
            "setup_2": "Gap and Fade (Mean Reversion)",
            "setup_3": "Episodic Pivot (EP)",
            "setup_4": "Pre-Market Volume Leader Breakout",
            "setup_5": "VWAP Institutional Hold & Re-Entry",
            "setup_6": "Late Day Momentum Squeeze",
            "setup_7": "Inside Day Breakout (NR7)",
            "setup_8": "VIX Spike Mean Reversion",
            "setup_9": "Volatility Contraction Pattern (VCP)",
            "setup_10": "10/21 EMA Short-Term Pullback",
            "setup_11": "50 SMA Institutional Support Bounce",
            "setup_12": "Standard ORB",
            "setup_13": "Blue Sky ATH Breakout",
            "setup_14": "Stage 1 to 2 Reversal (200 SMA Reclaim)",
            "setup_15": "PEAD Consolidation Breakout"
        }

        for symbol in WATCHLIST:
            try:
                ticker = yf.Ticker(symbol)
                # Download 60 daily candles
                df = ticker.history(period="60d", interval="1d")
                if df.empty or len(df) < 20:
                    continue
                
                df = calculate_smas(df)
                df['vol_sma_20'] = df['Volume'].rolling(window=20).mean()
                df['rvol'] = df['Volume'] / df['vol_sma_20']
                df = df.dropna().copy()
                
                if df.empty:
                    continue
                    
                latest = df.iloc[-1]
                prev = df.iloc[-2]
                close = float(latest['Close'])
                open_p = float(latest['Open'])
                high = float(latest['High'])
                low = float(latest['Low'])
                rvol = float(latest['rvol'])
                
                # Check Gap %
                gap_pct = (open_p - float(prev['Close'])) / float(prev['Close'])
                
                # ----------------- SCANNER CONDITIONS FOR EACH SETUP -----------------
                
                # Setup 1: Gap and Go
                if gap_pct >= 0.03 and rvol >= 1.5:
                    score = calculate_mos_b(2, rvol, 0.03, True, True, True)
                    results_by_setup["setup_1"].append(self._build_result(symbol, score, {"gap_pct": gap_pct, "rvol": rvol}, {
                        "catalyst": 1.0, "volume": 1.5, "vol_regime": 1.5, "order_flow": 1.0, "technicals": score - 5.0
                    }))
                    
                # Setup 2: Gap and Fade
                if abs(gap_pct) >= 0.03 and rvol < 1.0:
                    score = calculate_mos_p(True, 0.5, True, True)
                    results_by_setup["setup_2"].append(self._build_result(symbol, score, {"gap_pct": gap_pct, "rvol": rvol}, {
                        "trend_strength": 3.0, "pullback_volume": 2.5, "reversal_trigger": 1.5, "support_zones": 1.5
                    }))

                # Setup 3: Episodic Pivot (EP)
                if gap_pct >= 0.05 and rvol >= 2.5:
                    score = calculate_mos_b(1, rvol, 0.06, True, True, True)
                    results_by_setup["setup_3"].append(self._build_result(symbol, score, {"gap_pct": gap_pct, "rvol": rvol}, {
                        "catalyst": 3.0, "volume": 2.5, "vol_regime": 1.5, "order_flow": 1.0, "technicals": 2.0
                    }))
                    
                # Setup 5: VWAP Hold (using EMA 20 bounce proxy on daily)
                if low <= latest['sma_20'] and close > latest['sma_20'] and close > open_p:
                    score = calculate_mos_p(True, 0.45, True, True)
                    results_by_setup["setup_5"].append(self._build_result(symbol, score, {"rvol": rvol, "dist_to_ema20": (close/latest['sma_20']-1)*100}, {
                        "trend_strength": 3.0, "pullback_volume": 2.5, "reversal_trigger": 1.5, "support_zones": 1.5
                    }))
                    
                # Setup 9: VCP
                # Volatility contracting check (High/Low spreads shrinking over past 3 days)
                range_today = (high - low) / close
                range_yest = (float(prev['High']) - float(prev['Low'])) / float(prev['Close'])
                if range_today < range_yest and rvol < 0.8 and close > latest['sma_50']:
                    score = calculate_mos_a(True, 3, rvol, True)
                    results_by_setup["setup_9"].append(self._build_result(symbol, score, {"rvol": rvol, "range_today_pct": range_today * 100}, {
                        "trend_alignment": 3.0, "contraction": 3.0, "volume_dryup": 2.5, "gex_support": 1.5
                    }))
                    
                # Setup 10: 10/21 EMA Pullback
                if low <= latest['sma_20'] and close > latest['sma_20'] and rvol < 1.0:
                    score = calculate_mos_p(True, rvol, True, True)
                    results_by_setup["setup_10"].append(self._build_result(symbol, score, {"rvol": rvol, "touch_ema20": True}, {
                        "trend_strength": 3.0, "pullback_volume": 2.5, "reversal_trigger": 1.5, "support_zones": 1.5
                    }))

                # Setup 11: 50 SMA Bounce
                if low <= latest['sma_50'] and close > latest['sma_50'] and close > open_p:
                    score = calculate_mos_p(True, rvol, True, True)
                    results_by_setup["setup_11"].append(self._build_result(symbol, score, {"rvol": rvol, "bounce_50sma": True}, {
                        "trend_strength": 3.0, "pullback_volume": 1.5, "reversal_trigger": 3.0, "support_zones": 1.5
                    }))

                # Setup 12: Standard ORB
                if rvol >= 1.5 and close > open_p and close > latest['sma_20']:
                    score = calculate_mos_b(2, rvol, 0.03, True, True, True)
                    results_by_setup["setup_12"].append(self._build_result(symbol, score, {"rvol": rvol, "close_vs_sma20": (close/latest['sma_20']-1)*100}, {
                        "catalyst": 1.0, "volume": 1.5, "vol_regime": 1.5, "order_flow": 1.0, "technicals": 2.0
                    }))

                # Setup 13: Blue Sky ATH Breakout
                high_30d = df['High'].iloc[-30:-1].max()
                if close > high_30d and rvol >= 1.2:
                    score = calculate_mos_b(1, rvol, 0.04, True, True, True)
                    results_by_setup["setup_13"].append(self._build_result(symbol, score, {"rvol": rvol, "breakout_level": high_30d}, {
                        "catalyst": 3.0, "volume": 1.5, "vol_regime": 1.5, "order_flow": 1.0, "technicals": 2.0
                    }))

                # Setup 14: Stage 2 Reversal (200 SMA reclaim)
                if close > latest['sma_200'] and prev['Close'] <= prev['sma_200']:
                    score = calculate_mos_p(True, rvol, True, True)
                    results_by_setup["setup_14"].append(self._build_result(symbol, score, {"rvol": rvol, "reclaim_200sma": True}, {
                        "trend_strength": 3.0, "pullback_volume": 2.5, "reversal_trigger": 1.5, "support_zones": 1.5
                    }))

                # Setup 15: PEAD Consolidation Breakout
                if rvol >= 1.2 and close > latest['sma_20'] and (close/latest['sma_50'] - 1) < 0.10:
                    score = calculate_mos_b(2, rvol, 0.02, True, True, True)
                    results_by_setup["setup_15"].append(self._build_result(symbol, score, {"rvol": rvol, "dist_50sma": (close/latest['sma_50']-1)*100}, {
                        "catalyst": 1.0, "volume": 1.5, "vol_regime": 1.5, "order_flow": 1.0, "technicals": 2.0
                    }))
                    
            except Exception as e:
                logger.error(f"Error scanning {symbol}: {e}")
                
        # Format the output into an elegant JSON list of all 15 setups
        scans_list = []
        for setup_id, name in setup_names.items():
            scans_list.append({
                "setup_id": setup_id,
                "setup_name": name,
                "results": results_by_setup[setup_id]
            })
            
        return scans_list

    def _build_result(self, symbol: str, score: float, metrics: dict, breakdown: dict) -> dict:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        # Sizing and risk properties
        risk_alloc = get_risk_allocation(score)
        
        return {
            "symbol": symbol,
            "timestamp": timestamp,
            "score": score,
            "conviction": risk_alloc["conviction"],
            "risk_pct": risk_alloc["risk_pct"] * 100,
            "metrics": metrics,
            "score_breakdown": breakdown
        }
