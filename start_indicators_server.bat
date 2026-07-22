@echo off
title Aether Indicators API Server
echo ============================================================
echo        STARTING AETHER INDICATORS LOCAL API SERVER
echo ============================================================
echo.
echo Server will run at http://127.0.0.1:8080
echo Leave this window open while trading to see live RVOL and GEX
echo overlays on your Market Terminal chart.
echo.
uv run --with fastapi --with uvicorn --with yfinance --with numpy --with pandas --with pyyaml algo-engine/src/server.py
echo.
pause
