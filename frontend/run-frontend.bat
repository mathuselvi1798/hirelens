@echo off
setlocal
cd /d "%~dp0"
title NEXA AI Analyzer - web app

echo ==================================================
echo   NEXA web app starting
echo.
echo   App : http://localhost:3000
echo.
echo   The backend must also be running (run-backend.bat)
echo   Leave this window open. Ctrl+C stops the app.
echo ==================================================
echo.

call npm run dev
pause
