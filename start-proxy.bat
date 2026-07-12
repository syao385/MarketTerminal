@echo on
title Aether Market Terminal Proxy
echo ===================================================
echo Starting Aether Market Terminal Local Proxy Server...
echo ===================================================

where node
if %errorlevel% neq 0 (
  echo [ERROR] Node.js is not detected on your system.
  echo Please download and install it from: https://nodejs.org/
  echo (If you just installed it, please close all command prompt windows and try again.)
  echo.
  pause
  exit /b
)

if exist "C:\Program Files\nodejs\node.exe" (
  "C:\Program Files\nodejs\node.exe" proxy-server.js
) else (
  node proxy-server.js
)

if %errorlevel% neq 0 (
  echo.
  echo [WARNING] Proxy server exited with an error (code %errorlevel%).
  echo This usually happens because port 3000 is already in use.
  echo.
  echo Please check if:
  echo   1. You already have another proxy command prompt window open.
  echo   2. Another application is using port 3000.
  echo.
)
pause
