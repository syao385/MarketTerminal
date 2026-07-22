import numpy as np
import pandas as pd
from typing import List, Union

def calculate_time_slice_rvol(
    current_volume_today: float,
    historical_cumulative_volumes: Union[List[float], np.ndarray]
) -> float:
    """
    Calculates Time-Slice Relative Volume (RVOL_TS) for premarket or regular hours.
    
    Formula:
        RVOL_TS(t) = Cumulative Vol to time t today / Mean Cumulative Vol to time t over last 20 days
        
    Args:
        current_volume_today: Cumulative volume traded up to time t today.
        historical_cumulative_volumes: List/Array of cumulative volumes traded up to time t in the past (e.g. 20 days).
        
    Returns:
        rvol: Relative volume factor (e.g. 2.5 means 250% of historical average).
    """
    if not historical_cumulative_volumes:
        return 1.0
        
    mean_volume = np.mean(historical_cumulative_volumes)
    if mean_volume <= 0:
        return 1.0
        
    return float(current_volume_today / mean_volume)


def calculate_pm_to_adv_ratio(
    total_pm_volume: float,
    adv_30d: float
) -> float:
    """
    Calculates the ratio of total premarket volume to 30-day Average Daily Volume (ADV).
    
    Formula:
        PM/ADV Ratio = Total Premarket Volume / 30-Day ADV
    """
    if adv_30d <= 0:
        return 0.0
    return float(total_pm_volume / adv_30d)


def calculate_volume_pacing_acceleration(
    current_minute_volume: float,
    historical_minute_volumes_mean: float
) -> float:
    """
    Calculates volume acceleration (Acc_Vol) in a specific minute relative to historical average.
    
    Formula:
        Acc_Vol(m) = Volume in minute m today / Mean volume in minute m historically
    """
    if historical_minute_volumes_mean <= 0:
        return 1.0
    return float(current_minute_volume / historical_minute_volumes_mean)


def evaluate_rvol_rm_threshold(rvol_rm: float) -> dict:
    """
    Categorizes the Regular Hours Time-Slice RVOL (RVOL_RM) for breakout setup scoring.
    """
    if rvol_rm >= 4.0:
        return {"category": "Historic", "score_impact": 2.5, "conviction": "High-Conviction Breakout"}
    elif rvol_rm >= 2.0:
        return {"category": "Standard", "score_impact": 1.5, "conviction": "Moderate Breakout"}
    else:
        return {"category": "Weak", "score_impact": -1.0, "conviction": "Failed Volume Signature"}
