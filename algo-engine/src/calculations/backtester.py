import os
import yaml
import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import logging

from calculations.scorecards import calculate_mos_b, calculate_mos_a, calculate_mos_p, get_risk_allocation

logger = logging.getLogger("AetherBacktester")

CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "config", "setups.yaml"))

class PlaybookBacktester:
    def __init__(self):
        self.config = {}
        self.load_setup_configs()

    def load_setup_configs(self):
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, 'r') as f:
                    self.config = yaml.safe_load(f)
                    logger.info("Loaded setup configurations for backtester.")
            except Exception as e:
                logger.error(f"Failed to load configurations: {e}")

    def run_backtest(
        self,
        symbol: str,
        setup_id: str,
        start_date: str = None,
        end_date: str = None,
        initial_capital: float = 100000.0
    ) -> dict:
        """
        Runs a historical backtest of a specific playbook setup.
        """
        symbol = symbol.upper().strip()
        setup_id = setup_id.lower().strip()
        
        # Load setup config
        setup_conf = self.config.get("setups", {}).get(setup_id)
        if not setup_conf:
            return {"success": False, "error": f"Configuration for {setup_id} not found."}
            
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365 * 2)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
            
        try:
            ticker = yf.Ticker(symbol)
            # Fetch daily candles
            df = ticker.history(start=start_date, end=end_date)
            if df.empty or len(df) < 50:
                return {"success": False, "error": f"Insufficient historical data for {symbol}"}
                
            # Compute technical indicators
            df['sma_20'] = df['Close'].rolling(window=20).mean()
            df['sma_50'] = df['Close'].rolling(window=50).mean()
            df['sma_200'] = df['Close'].rolling(window=200).mean()
            
            # 20-period volume SMA for relative volume calculations
            df['vol_sma_20'] = df['Volume'].rolling(window=20).mean()
            df['rvol'] = df['Volume'] / df['vol_sma_20']
            
            # Simple True Range and ATR (for targets and stops)
            high_low = df['High'] - df['Low']
            high_close = (df['High'] - df['Close'].shift()).abs()
            low_close = (df['Low'] - df['Close'].shift()).abs()
            df['tr'] = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            df['atr'] = df['tr'].rolling(window=14).mean()
            
            # Clean NaN values from indicator calculations
            df = df.dropna().copy()
            
        except Exception as e:
            return {"success": False, "error": f"Failed to fetch or compute indicators: {str(e)}"}
            
        # Simulate trading
        capital = initial_capital
        position_shares = 0.0
        entry_price = 0.0
        stop_loss = 0.0
        pt_target_1 = 0.0
        pt_target_2 = 0.0
        has_taken_partial_1 = False
        has_taken_partial_2 = False
        
        trades_log = []
        equity_curve = []
        
        # Loop day-by-day
        for i in range(len(df)):
            row = df.iloc[i]
            date_str = df.index[i].strftime('%Y-%m-%d')
            close = float(row['Close'])
            high = float(row['High'])
            low = float(row['Low'])
            rvol = float(row['rvol'])
            
            # 1. Manage Active Position
            if position_shares > 0:
                # Check Stop Loss
                if low <= stop_loss:
                    exit_price = stop_loss
                    pnl = (exit_price - entry_price) * position_shares
                    capital += exit_price * position_shares
                    
                    trades_log.append({
                        "entry_date": entry_date,
                        "exit_date": date_str,
                        "entry_price": entry_price,
                        "exit_price": exit_price,
                        "shares": position_shares,
                        "pnl": pnl,
                        "return_pct": (exit_price / entry_price - 1.0) * 100,
                        "exit_reason": "Stop Loss"
                    })
                    position_shares = 0.0
                    logger.info(f"[{date_str}] STOP LOSS triggered at {exit_price:.2f}. PnL: ${pnl:.2f}")
                    equity_curve.append(capital)
                    continue
                    
                # Check Partial Profit Target 1
                if pt_target_1 > 0 and high >= pt_target_1 and not has_taken_partial_1:
                    sell_shares = position_shares * setup_conf.get("ptp_1_sell_ratio", 0.5)
                    capital += pt_target_1 * sell_shares
                    position_shares -= sell_shares
                    has_taken_partial_1 = True
                    # Move stop loss to breakeven (standard playbook rule)
                    stop_loss = entry_price
                    logger.info(f"[{date_str}] PARTIAL TARGET 1 hit at {pt_target_1:.2f}. Sold {sell_shares:.1f} shares. Stop moved to breakeven.")
                    
                # Check Partial Profit Target 2
                if pt_target_2 > 0 and high >= pt_target_2 and not has_taken_partial_2:
                    sell_shares = position_shares * setup_conf.get("ptp_2_sell_ratio", 0.5)
                    capital += pt_target_2 * sell_shares
                    position_shares -= sell_shares
                    has_taken_partial_2 = True
                    logger.info(f"[{date_str}] PARTIAL TARGET 2 hit at {pt_target_2:.2f}. Sold {sell_shares:.1f} shares.")
                    
                # Check Trailing Stop Reversal or End of History Exit
                # In daily simulation, we check trailing MA conditions
                trail_indicator = setup_conf.get("exit_trailing_ma", "daily_10_ema")
                # Simple trailing stop proxy: if close drops below SMA 50 or 20 days low
                if trail_indicator == "daily_50_sma" and close < row['sma_50']:
                    exit_price = close
                    pnl = (exit_price - entry_price) * position_shares
                    capital += exit_price * position_shares
                    trades_log.append({
                        "entry_date": entry_date,
                        "exit_date": date_str,
                        "entry_price": entry_price,
                        "exit_price": exit_price,
                        "shares": position_shares + (sell_shares if has_taken_partial_1 else 0), # track total
                        "pnl": pnl,
                        "return_pct": (exit_price / entry_price - 1.0) * 100,
                        "exit_reason": "Trailing Stop"
                    })
                    position_shares = 0.0
                    logger.info(f"[{date_str}] TRAILING STOP triggered at {exit_price:.2f}. PnL: ${pnl:.2f}")
                    
                # Exit at the final bar of history
                elif i == len(df) - 1:
                    exit_price = close
                    pnl = (exit_price - entry_price) * position_shares
                    capital += exit_price * position_shares
                    trades_log.append({
                        "entry_date": entry_date,
                        "exit_date": date_str,
                        "entry_price": entry_price,
                        "exit_price": exit_price,
                        "shares": position_shares,
                        "pnl": pnl,
                        "return_pct": (exit_price / entry_price - 1.0) * 100,
                        "exit_reason": "End of History"
                    })
                    position_shares = 0.0
                    
            # 2. Evaluate Setup Entry Triggers
            else:
                is_trigger = False
                mos_score = 0.0
                
                # Setup 12: Standard ORB
                if setup_id == "setup_12":
                    # Check volume pacing and pivot breakout proxy
                    if rvol >= setup_conf.get("rvol_rm_threshold", 2.0) and close > row['sma_20']:
                        is_trigger = True
                        # MOS-B calculation
                        mos_score = calculate_mos_b(
                            catalyst_tier=2,
                            rvol_ts=rvol,
                            pm_adv=0.03,
                            is_below_flip=True,
                            is_delta_sweep=True,
                            is_technical_breakout=True
                        )
                        
                # Setup 13: All-Time High Breakout
                elif setup_id == "setup_13":
                    # Check if close is breaking out near highest high of past 30 days
                    high_30d = df['High'].iloc[max(0, i-30):i].max() if i > 0 else close
                    if close > high_30d and rvol >= setup_conf.get("rvol_20d_multiplier", 1.5):
                        is_trigger = True
                        mos_score = calculate_mos_b(
                            catalyst_tier=1,
                            rvol_ts=rvol,
                            pm_adv=0.04,
                            is_below_flip=True,
                            is_delta_sweep=True,
                            is_technical_breakout=True
                        )
                        
                # Setup 14: Stage 2 Reversal
                elif setup_id == "setup_14":
                    # Reversal cross above 200 SMA
                    if close > row['sma_200'] and df['Close'].iloc[max(0, i-1)] <= row['sma_200'] and rvol >= setup_conf.get("rvol_multiplier", 1.5):
                        is_trigger = True
                        mos_score = calculate_mos_p(
                            is_bullish_stack=True,
                            pullback_vol_adv_ratio=0.5,
                            is_reversal_candle=True,
                            aligned_support=True
                        )
                        
                # Fallback / Default breakout check
                elif rvol >= 2.0 and close > row['sma_20'] and close > row['sma_50']:
                    is_trigger = True
                    mos_score = calculate_mos_b(2, rvol, 0.02, True, True, True)

                # Process Trigger Entry
                if is_trigger:
                    risk_rules = get_risk_allocation(mos_score)
                    risk_pct = risk_rules["risk_pct"]
                    
                    if risk_pct > 0.0:
                        entry_price = close
                        entry_date = date_str
                        has_taken_partial_1 = False
                        has_taken_partial_2 = False
                        
                        # Stop Loss is set to 2 ATRs below entry (standard playbook default)
                        atr = float(row['atr']) if not pd.isna(row['atr']) else (close * 0.02)
                        stop_loss = entry_price - (atr * 2.0)
                        risk_per_share = entry_price - stop_loss
                        
                        # Sizing: Risk capital (capital * risk_pct) divided by risk per share
                        risk_amount = capital * risk_pct
                        position_shares = float(np.floor(risk_amount / risk_per_share))
                        
                        # Ensure we do not exceed capital or 100% allocation
                        if position_shares * entry_price > capital * risk_rules["allocation_pct"]:
                            position_shares = float(np.floor((capital * risk_rules["allocation_pct"]) / entry_price))
                            
                        if position_shares > 0:
                            capital -= position_shares * entry_price
                            
                            # Partial targets
                            pt_target_1 = entry_price + (risk_per_share * setup_conf.get("ptp_1_r", 1.5))
                            pt_target_2 = entry_price + (risk_per_share * setup_conf.get("ptp_2_r", 3.0))
                            
                            logger.info(f"[{date_str}] ENTRY triggered for {setup_id}. Price: {entry_price:.2f}. Size: {position_shares} shares. Stop: {stop_loss:.2f}. PT1: {pt_target_1:.2f}. MOS: {mos_score:.1f}")

            equity_curve.append(capital + (position_shares * close))
            
        # Compile stats
        total_trades = len(trades_log)
        winning_trades = [t for t in trades_log if t["pnl"] > 0]
        win_rate = (len(winning_trades) / total_trades * 100.0) if total_trades > 0 else 0.0
        
        total_pnl = sum([t["pnl"] for t in trades_log])
        profit_factor = 1.0
        gross_profits = sum([t["pnl"] for t in trades_log if t["pnl"] > 0])
        gross_losses = abs(sum([t["pnl"] for t in trades_log if t["pnl"] < 0]))
        if gross_losses > 0:
            profit_factor = gross_profits / gross_losses
            
        # Drawdown calculation
        equity_series = pd.Series(equity_curve)
        cum_max = equity_series.cummax()
        drawdown = (equity_series - cum_max) / cum_max
        max_drawdown = float(drawdown.min() * 100.0) if not drawdown.empty else 0.0

        return {
            "success": True,
            "symbol": symbol,
            "setup_id": setup_id,
            "initial_capital": initial_capital,
            "final_capital": capital + (position_shares * close if position_shares > 0 else 0.0),
            "total_trades": total_trades,
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "max_drawdown_pct": max_drawdown,
            "trades": trades_log
        }
