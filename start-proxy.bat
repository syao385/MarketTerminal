@echo off
title Aether Market Terminal Proxy
echo ===================================================
echo Starting Aether Market Terminal Local Proxy Server...
echo ===================================================
node proxy-server.js
if %errorlevel% neq 0 (
  echo.
  echo [ERROR] Failed to start Node.js. Is Node.js installed?
  echo Please download it from https://nodejs.org/
  echo.
)
pause
