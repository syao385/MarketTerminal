import pandas as pd
import numpy as np
from typing import Dict, List, Any

def calculate_smas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates SMA 20, 50, and 200.
    """
    df['sma_20'] = df['Close'].rolling(window=20).mean()
    df['sma_50'] = df['Close'].rolling(window=50).mean()
    df['sma_200'] = df['Close'].rolling(window=200).mean()
    return df


def find_unmitigated_gaps(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Finds unmitigated daily gaps.
    A gap is unmitigated until a daily close goes beyond the boundary:
    - Bullish Gap: Close goes below the gap bottom.
    - Bearish Gap: Close goes above the gap top.
    """
    gaps = []
    
    for i in range(1, len(df)):
        prev = df.iloc[i-1]
        curr = df.iloc[i]
        
        # Bullish Gap (Gap Up)
        if curr['Low'] > prev['High']:
            gaps.append({
                "type": "bullish",
                "top": float(curr['Low']),
                "bottom": float(prev['High']),
                "start_idx": i,
                "mitigated": False,
                "mitigated_idx": None
            })
        # Bearish Gap (Gap Down)
        elif curr['High'] < prev['Low']:
            gaps.append({
                "type": "bearish",
                "top": float(prev['Low']),
                "bottom": float(curr['High']),
                "start_idx": i,
                "mitigated": False,
                "mitigated_idx": None
            })
            
        # Check mitigation for all active gaps
        close = curr['Close']
        for gap in gaps:
            if not gap["mitigated"] and gap["start_idx"] < i:
                if gap["type"] == "bullish" and close < gap["bottom"]:
                    gap["mitigated"] = True
                    gap["mitigated_idx"] = i
                elif gap["type"] == "bearish" and close > gap["top"]:
                    gap["mitigated"] = True
                    gap["mitigated_idx"] = i
                    
    # Return only unmitigated gaps
    return [g for g in gaps if not g["mitigated"]]


def find_unmitigated_fvgs(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Finds unmitigated Fair Value Gaps (FVG) using a 3-candle sequence.
    An FVG is unmitigated until a daily close goes beyond the FVG boundary:
    - Bullish FVG (Candle 1 High < Candle 3 Low): Close goes below Candle 1 High.
    - Bearish FVG (Candle 1 Low > Candle 3 High): Close goes above Candle 1 Low.
    """
    fvgs = []
    
    for i in range(2, len(df)):
        c1 = df.iloc[i-2]
        c2 = df.iloc[i-1]
        c3 = df.iloc[i]
        
        # Bullish FVG
        if c1['High'] < c3['Low']:
            fvgs.append({
                "type": "bullish",
                "top": float(c3['Low']),
                "bottom": float(c1['High']),
                "start_idx": i-1,
                "mitigated": False,
                "mitigated_idx": None
            })
        # Bearish FVG
        elif c1['Low'] > c3['High']:
            fvgs.append({
                "type": "bearish",
                "top": float(c1['Low']),
                "bottom": float(c3['High']),
                "start_idx": i-1,
                "mitigated": False,
                "mitigated_idx": None
            })
            
        # Check mitigation for all active FVGs
        close = c3['Close']
        for fvg in fvgs:
            if not fvg["mitigated"] and fvg["start_idx"] < i:
                if fvg["type"] == "bullish" and close < fvg["bottom"]:
                    fvg["mitigated"] = True
                    fvg["mitigated_idx"] = i
                elif fvg["type"] == "bearish" and close > fvg["top"]:
                    fvg["mitigated"] = True
                    fvg["mitigated_idx"] = i
                    
    # Return only unmitigated FVGs
    return [f for f in fvgs if not f["mitigated"]]
