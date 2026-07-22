import logging
from typing import List, Dict, Any

from calculations.backtester import PlaybookBacktester

logger = logging.getLogger("AetherOptimizer")

class SetupParameterOptimizer:
    def __init__(self):
        self.backtester = PlaybookBacktester()

    def optimize_setup_parameters(
        self,
        symbol: str,
        setup_id: str,
        start_date: str = None,
        end_date: str = None,
        rvol_range: List[float] = [1.5, 2.0, 3.0],
        ptp_r_range: List[float] = [1.5, 2.0, 3.0],
        initial_capital: float = 100000.0
    ) -> Dict[str, Any]:
        """
        Runs a grid sweep of parameters to optimize win rates and net profit for a given setup.
        """
        best_capital = 0.0
        best_params = {}
        best_results = {}
        all_runs = []

        logger.info(f"Starting parameter sweep optimization for {symbol} - {setup_id}...")

        # Grid search sweep
        for rvol in rvol_range:
            for ptp_r in ptp_r_range:
                # Dynamically inject/overwrite the configuration dictionary parameters
                setup_conf = self.backtester.config.get("setups", {}).get(setup_id)
                if not setup_conf:
                    continue
                
                # Apply parameters to config memory
                original_rvol = setup_conf.get("rvol_rm_threshold")
                original_ptp1 = setup_conf.get("ptp_1_r")
                
                # Override
                if "rvol_rm_threshold" in setup_conf:
                    setup_conf["rvol_rm_threshold"] = rvol
                if "rvol_multiplier" in setup_conf:
                    setup_conf["rvol_multiplier"] = rvol
                setup_conf["ptp_1_r"] = ptp_r
                
                # Execute Backtest
                result = self.backtester.run_backtest(
                    symbol=symbol,
                    setup_id=setup_id,
                    start_date=start_date,
                    end_date=end_date,
                    initial_capital=initial_capital
                )
                
                # Restore original configuration
                if original_rvol is not None:
                    if "rvol_rm_threshold" in setup_conf:
                        setup_conf["rvol_rm_threshold"] = original_rvol
                    if "rvol_multiplier" in setup_conf:
                        setup_conf["rvol_multiplier"] = original_rvol
                setup_conf["ptp_1_r"] = original_ptp1
                
                if result.get("success"):
                    final_cap = result["final_capital"]
                    run_summary = {
                        "rvol_threshold": rvol,
                        "ptp_1_r": ptp_r,
                        "final_capital": final_cap,
                        "net_profit": final_cap - initial_capital,
                        "total_trades": result["total_trades"],
                        "win_rate": result["win_rate"],
                        "profit_factor": result["profit_factor"],
                        "max_drawdown_pct": result["max_drawdown_pct"]
                    }
                    all_runs.append(run_summary)
                    
                    if final_cap > best_capital:
                        best_capital = final_cap
                        best_params = {"rvol_threshold": rvol, "ptp_1_r": ptp_r}
                        best_results = run_summary

        return {
            "success": len(all_runs) > 0,
            "symbol": symbol,
            "setup_id": setup_id,
            "best_parameters": best_params,
            "best_run_results": best_results,
            "all_runs_summary": all_runs
        }
