@echo off
title Aether Playbook Backtester Validator
echo ============================================================
echo      RUNNING HISTORICAL BACKTEST & PARAMETER SWEEP CHECK
echo ============================================================
echo.
uv run --python 3.12 --with pyyaml --with pandas --with numpy --with yfinance python algo-engine/verify_milestone_2.py
echo.
echo ============================================================
echo   Validation finished.
echo ============================================================
pause
