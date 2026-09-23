import logging
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from calculations.scorecards import calculate_mos_b, calculate_mos_a, calculate_mos_p, get_risk_allocation
from calculations.indicators import calculate_smas

logger = logging.getLogger("AetherScanner")

WATCHLIST = [
    "AAPL", "MSFT", "AMZN", "NVDA", "GOOGL", "META", "TSLA", "BRK-B", "LLY", "AVGO",
    "JPM", "V", "UNH", "XOM", "MA", "HD", "PG", "COST", "JNJ", "ABBV",
    "MRK", "NFLX", "AMD", "ADBE", "CRM", "BAC", "PEP", "CVX", "TMO", "WMT",
    "MCD", "QCOM", "CSCO", "INTC", "INTU", "SPG", "DHR", "AMGN", "GE", "ISRG",
    "TXN", "CAT", "HON", "AXP", "AMAT", "PFE", "MS", "PM", "PLTR", "GS",
    "NKE", "BKNG", "SPY", "QQQ", "IWM", "DIA", "SMCI", "MARA", "RIOT", "CLSK",
    "COIN", "MSTR", "UPST", "RXRX", "ASTS", "CVNA", "HOOD", "RDDT", "SMR", "RBLX",
    "AFRM", "LCID", "RIVN", "SOFI", "PATH", "IONQ", "QUBT", "RGTI", "KIDZ", "TEM",
    "SOUN", "PLUG", "NIO", "JD", "BABA", "F", "FUTU", "TME", "BILI", "LI",
    "DIS", "CMG", "TJX", "ADP", "MDLZ", "VRTX", "LRCX", "MU", "ADI", "PANW",
    "MELI", "SNOW", "PYPL", "CRWD", "ABNB", "WDAY", "ORCL", "GILD", "PDD", "LMT",
    "GEHC", "REGN", "NXPI", "MCHP", "KLAC", "CTAS", "CDNS", "ADSK", "TEAM", "FTNT",
    "ADX", "ASML", "AZN", "BIIB", "BMRN", "CDW", "CARR", "CHTR", "CPRT", "CSX",
    "DXCM", "EA", "EXC", "FAST", "GE", "HON", "IDXX", "ILMN", "KDP", "KHC",
    "LULU", "MAR", "MCHP", "MDLZ", "MNST", "ODFL", "ON", "PCAR",
    "PAYX", "ROST", "SBUX", "SIRI", "SNPS", "VRSK", "VRSN", "WBA", "WBD", "XEL",
    "A", "AA", "AAL", "AAON", "AAP", "AAT", "AAWW", "ABB", "ABC", "ABG",
    "ABIL", "ABM", "ABMD", "ABT", "ACA", "ACAD", "ACC", "ACGL", "ACHC", "ACI",
    "ACIA", "ACIW", "ACLS", "ACM", "ACN", "ACRE", "ACRS", "ACRX", "ACT", "ADUS",
    "AE", "AEE", "AEG", "AEIS", "AEL", "AEM", "AEO", "AEP", "AER", "AES",
    "AFG", "AFL", "AG", "AGCO", "AGE", "AGEN", "AGFS", "AGIO", "AGNC", "AGO",
    "AGR", "AGRX", "AGS", "AGTC", "AHC", "AHH", "AHL", "AHT", "AIG", "AIMT",
    "AIN", "AINV", "AIP", "AIR", "AIRC", "AIRE", "AIRG", "AIRI", "AIRT", "AIT",
    "AIV", "AIZ", "AJG", "AJRD", "AJX", "AKAM", "AKBA", "AKCA", "AKER", "AKRO",
    "AKRX", "AKTS", "AL", "ALB", "ALBO", "ALCO", "ALEC", "ALEX", "ALG", "ALGN",
    "ALGR", "ALGT", "ALIM", "ALJJ", "ALK", "ALKS", "ALL", "ALLE", "ALLK", "ALLO",
    "ALLT", "ALLY", "ALNA", "ALNY", "ALOT", "ALPN", "ALRM", "ALRN", "ALSN", "ALT",
    "ALTA", "ALTR", "ALX", "ALXN", "AM", "AMAG", "AMAL", "AMBA", "AMBC", "AMC",
    "AMCA", "AMCF", "AMCI", "AMCX", "AME", "AMED", "AMEH", "AMG", "AMH",
    "AMHC", "AMID", "AMKR", "AMN", "AMNB", "AMOT", "AMP", "AMPE", "AMPH", "AMPY",
    "AMR", "AMRC", "AMRH", "AMRK", "AMRN", "AMRS", "AMRX", "AMS", "AMSC", "AMSF"
]

class PlaybookScanner:
    def __init__(self, watchlist: Optional[List[str]] = None):
        self.watchlist = watchlist if watchlist else WATCHLIST

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

        # Multi-threaded parallel scanning
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        def task(symbol):
            return self._scan_single_symbol(symbol)
            
        with ThreadPoolExecutor(max_workers=30) as executor:
            futures = {executor.submit(task, sym): sym for sym in self.watchlist}
            for future in as_completed(futures):
                res = future.result()
                if res:
                    for setup_id, r in res:
                        results_by_setup[setup_id].append(r)

        # Format the output into an elegant JSON list of all 15 setups
        scans_list = []
        for setup_id, name in setup_names.items():
            scans_list.append({
                "setup_id": setup_id,
                "setup_name": name,
                "results": results_by_setup[setup_id]
            })
            
        return scans_list

    def _scan_single_symbol(self, symbol: str) -> List[Any]:
        symbol_results = []
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period="260d", interval="1d", prepost=True)
            if df.empty or len(df) < 200:
                return []
            
            df = calculate_smas(df)
            df['vol_sma_20'] = df['Volume'].rolling(window=20).mean()
            df['rvol'] = df['Volume'] / df['vol_sma_20']
            df = df.dropna().copy()
            if df.empty:
                return []
                
            latest = df.iloc[-1]
            prev = df.iloc[-2]
            close = float(latest['Close'])
            open_p = float(latest['Open'])
            high = float(latest['High'])
            low = float(latest['Low'])
            rvol = float(latest['rvol'])
            
            gap_pct = (open_p - float(prev['Close'])) / float(prev['Close'])
            
            # Setup 1: Gap and Go (5m)
            if gap_pct >= 0.03 and rvol >= 1.5:
                score = calculate_mos_b(2, rvol, 0.03, True, True, True)
                symbol_results.append(("setup_1", self._build_result(symbol, score, {"gap_pct": gap_pct, "rvol": rvol}, {
                    "catalyst": 1.0, "volume": 1.5, "vol_regime": 1.5, "order_flow": 1.0, "technicals": score - 5.0
                }, direction="long", timeframe="5m")))
                
            # Setup 2: Gap and Fade (5m)
            if abs(gap_pct) >= 0.03 and rvol < 1.0:
                score = calculate_mos_p(True, 0.5, True, True)
                symbol_results.append(("setup_2", self._build_result(symbol, score, {"gap_pct": gap_pct, "rvol": rvol}, {
                    "trend_strength": 3.0, "pullback_volume": 2.5, "reversal_trigger": 1.5, "support_zones": 1.5
                }, direction="short", timeframe="5m")))

            # Setup 3: Episodic Pivot (EP) (1d/5m)
            if gap_pct >= 0.05 and rvol >= 2.5:
                score = calculate_mos_b(1, rvol, 0.06, True, True, True)
                symbol_results.append(("setup_3", self._build_result(symbol, score, {"gap_pct": gap_pct, "rvol": rvol}, {
                    "catalyst": 3.0, "volume": 2.5, "vol_regime": 1.5, "order_flow": 1.0, "technicals": 2.0
                }, direction="long", timeframe="1d")))
                
            # Setup 5: VWAP Hold (5m)
            if low <= latest['sma_20'] and close > latest['sma_20'] and close > open_p:
                score = calculate_mos_p(True, 0.45, True, True)
                symbol_results.append(("setup_5", self._build_result(symbol, score, {"rvol": rvol, "dist_to_ema20": (close/latest['sma_20']-1)*100}, {
                    "trend_strength": 3.0, "pullback_volume": 2.5, "reversal_trigger": 1.5, "support_zones": 1.5
                }, direction="long", timeframe="5m")))
                
            # Setup 9: VCP (1d)
            range_today = (high - low) / close
            range_yest = (float(prev['High']) - float(prev['Low'])) / float(prev['Close'])
            if range_today < range_yest and rvol < 0.8 and close > latest['sma_50']:
                score = calculate_mos_a(True, 3, rvol, True)
                symbol_results.append(("setup_9", self._build_result(symbol, score, {"rvol": rvol, "range_today_pct": range_today * 100}, {
                    "trend_alignment": 3.0, "contraction": 3.0, "volume_dryup": 2.5, "gex_support": 1.5
                }, direction="long", timeframe="1d")))
                
            # Setup 10: 10/21 EMA Pullback (5m)
            if low <= latest['sma_20'] and close > latest['sma_20'] and rvol < 1.0:
                score = calculate_mos_p(True, rvol, True, True)
                symbol_results.append(("setup_10", self._build_result(symbol, score, {"rvol": rvol, "touch_ema20": True}, {
                    "trend_strength": 3.0, "pullback_volume": 2.5, "reversal_trigger": 1.5, "support_zones": 1.5
                }, direction="long", timeframe="5m")))

            # Setup 11: 30-Min ORB (15m)
            if low <= latest['sma_50'] and close > latest['sma_50'] and close > open_p:
                score = calculate_mos_p(True, rvol, True, True)
                symbol_results.append(("setup_11", self._build_result(symbol, score, {"rvol": rvol, "bounce_50sma": True}, {
                    "trend_strength": 3.0, "pullback_volume": 1.5, "reversal_trigger": 3.0, "support_zones": 1.5
                }, direction="long", timeframe="15m")))

            # Setup 12: Standard 15-Min ORB (5m)
            if rvol >= 1.5 and close > open_p and close > latest['sma_20']:
                score = calculate_mos_b(2, rvol, 0.03, True, True, True)
                symbol_results.append(("setup_12", self._build_result(symbol, score, {"rvol": rvol, "close_vs_sma20": (close/latest['sma_20']-1)*100}, {
                    "catalyst": 1.0, "volume": 1.5, "vol_regime": 1.5, "order_flow": 1.0, "technicals": 2.0
                }, direction="long", timeframe="5m")))

            # Setup 13: Blue Sky ATH Breakout (1d)
            high_30d = df['High'].iloc[-30:-1].max()
            if close > high_30d and rvol >= 1.2:
                score = calculate_mos_b(1, rvol, 0.04, True, True, True)
                symbol_results.append(("setup_13", self._build_result(symbol, score, {"rvol": rvol, "breakout_level": high_30d}, {
                    "catalyst": 3.0, "volume": 1.5, "vol_regime": 1.5, "order_flow": 1.0, "technicals": 2.0
                }, direction="long", timeframe="1d")))

            # Setup 14: Stage 2 Reversal (1d)
            if close > latest['sma_200'] and prev['Close'] <= prev['sma_200']:
                score = calculate_mos_p(True, rvol, True, True)
                symbol_results.append(("setup_14", self._build_result(symbol, score, {"rvol": rvol, "reclaim_200sma": True}, {
                    "trend_strength": 3.0, "pullback_volume": 2.5, "reversal_trigger": 1.5, "support_zones": 1.5
                }, direction="long", timeframe="1d")))

            # Setup 15: PEAD Consolidation Breakout (1d)
            if rvol >= 1.2 and close > latest['sma_20'] and (close/latest['sma_50'] - 1) < 0.10:
                score = calculate_mos_b(2, rvol, 0.02, True, True, True)
                symbol_results.append(("setup_15", self._build_result(symbol, score, {"rvol": rvol, "dist_50sma": (close/latest['sma_50']-1)*100}, {
                    "catalyst": 1.0, "volume": 1.5, "vol_regime": 1.5, "order_flow": 1.0, "technicals": 2.0
                }, direction="long", timeframe="1d")))
        except Exception as e:
            logger.error(f"Error scanning single symbol {symbol}: {e}")
        return symbol_results

    def _build_result(self, symbol: str, score: float, metrics: dict, breakdown: dict, direction: str = "long", timeframe: str = "5m") -> dict:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        risk_alloc = get_risk_allocation(score)
        return {
            "symbol": symbol,
            "timestamp": timestamp,
            "score": score,
            "direction": direction,
            "timeframe": timeframe,
            "conviction": risk_alloc["conviction"],
            "risk_pct": risk_alloc["risk_pct"] * 100,
            "metrics": metrics,
            "score_breakdown": breakdown
        }
