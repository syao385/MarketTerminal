import sys
import os
import logging

# Ensure src/ is in the import path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from calculations.backtester import PlaybookBacktester
from calculations.optimizer import SetupParameterOptimizer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Milestone2Verification")

def run_verification():
    logger.info("============================================================")
    logger.info("       RUNNING MILESTONE 2 REGISTRY AND BACKTEST VERIFICATION")
    logger.info("============================================================")
    
    symbol = "NVDA"
    setup_id = "setup_12" # Standard ORB
    
    # 1. Test Historical Backtester
    logger.info(f"\n1. Executing PlaybookBacktester on {symbol} for {setup_id}...")
    backtester = PlaybookBacktester()
    
    # Set dates covering the past year
    start_date = "2024-01-01"
    end_date = "2026-01-01"
    
    res = backtester.run_backtest(
        symbol=symbol,
        setup_id=setup_id,
        start_date=start_date,
        end_date=end_date,
        initial_capital=100000.0
    )
    
    if res.get("success"):
        logger.info("SUCCESS: Backtester executed successfully.")
        logger.info(f"Initial Capital: ${res['initial_capital']:,.2f}")
        logger.info(f"Final Capital:   ${res['final_capital']:,.2f}")
        logger.info(f"Total Trades:    {res['total_trades']}")
        logger.info(f"Win Rate:        {res['win_rate']:.2f}%")
        logger.info(f"Profit Factor:   {res['profit_factor']:.2f}")
        logger.info(f"Max Drawdown:    {res['max_drawdown_pct']:.2f}%")
    else:
        logger.error(f"FAILURE: Backtester failed with error: {res.get('error')}")
        sys.exit(1)
        
    # 2. Test Parameter Sweep Optimizer
    logger.info(f"\n2. Executing SetupParameterOptimizer on {symbol} for {setup_id}...")
    optimizer = SetupParameterOptimizer()
    opt_res = optimizer.optimize_setup_parameters(
        symbol=symbol,
        setup_id=setup_id,
        start_date=start_date,
        end_date=end_date,
        rvol_range=[1.5, 3.0],
        ptp_r_range=[1.5, 3.0]
    )
    
    if opt_res.get("success"):
        logger.info("SUCCESS: Optimizer executed successfully.")
        logger.info(f"Best parameters found: {opt_res['best_parameters']}")
        logger.info(f"Best run net profit:  ${opt_res['best_run_results']['net_profit']:,.2f}")
        logger.info(f"Total combinations tested: {len(opt_res['all_runs_summary'])}")
    else:
        logger.error(f"FAILURE: Optimizer failed with error: {opt_res.get('error')}")
        sys.exit(1)
        
    logger.info("\n============================================================")
    logger.info("   Milestone 2 Verification Passed successfully!")
    logger.info("============================================================")

if __name__ == "__main__":
    run_verification()
