@echo off
title Aether Market Terminal Proxy
echo ===================================================
echo Starting Aether Market Terminal Local Proxy Server...
echo ===================================================

where node >nul 2>nul
if %errorlevel% equ 0 goto node_ok

echo [ERROR] Node.js is not detected on your system.
echo Please download and install it from: https://nodejs.org/
echo (If you just installed it, please close all command prompt windows and try again.)
echo.
pause
exit /b

:node_ok
if exist "C:\Program Files\nodejs\node.exe" goto use_absolute

node --max-http-header-size=80000 proxy-server.js
goto check_error

:use_absolute
"C:\Program Files\nodejs\node.exe" --max-http-header-size=80000 proxy-server.js

:check_error
if %errorlevel% equ 0 goto end

echo.
echo [WARNING] Proxy server exited with an error (code %errorlevel%).
echo This usually happens because port 3000 is already in use.
echo.
echo Please check if:
echo   1. You already have another proxy command prompt window open.
echo   2. Another application is using port 3000.
echo.
pause

:end
