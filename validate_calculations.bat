@echo off
title Aether Calculations Validator
echo ============================================================
echo      RUNNING PLAYBOOK CALCULATIONS MATHEMATICAL CHECK
echo ============================================================
echo.
uv run --with pandas --with numpy --with yfinance algo-engine/verify_playbook_calculations.py
echo.
echo ============================================================
echo   Validation finished.
echo ============================================================
pause
