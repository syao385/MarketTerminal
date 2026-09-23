@echo off
title MarketTerminal Backend Engine
echo ========================================================
echo Starting MarketTerminal FastAPI Backend Engine...
echo ========================================================
cd /d "%~dp0"

echo [1/3] Clearing port 8080 from previous sessions...
powershell -Command "Get-NetTCPConnection -LocalPort 8080 -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess | Where-Object { $_ -gt 0 } | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }" >nul 2>&1

echo [2/3] Starting FastAPI server process...
start "MarketTerminal Server Process" cmd /k "cd /d ""%~dp0algo-engine\src"" && uv run --python 3.12 --with fastapi --with uvicorn --with yfinance --with numpy --with pandas --with pyyaml --with httpx python server.py"

echo [3/3] Waiting 5 seconds for server startup and database connection...
ping 127.0.0.1 -n 6 > nul

echo Opening Web UI at http://127.0.0.1:8080 ...
start http://127.0.0.1:8080/

echo.
echo ========================================================
echo SYSTEM READY! Server is running at http://127.0.0.1:8080
echo Keep the server command window open while trading.
echo ========================================================
pause
