@echo off
title NEXA AI Analyzer - API server
cd /d "%~dp0backend" 2>nul || (echo Could not find the backend folder. & pause & exit /b 1)
if not exist ".venv\Scripts\python.exe" (
  echo Virtual environment missing. Run setup-backend.bat first.
  pause
  exit /b 1
)
echo ==================================================
echo   NEXA API starting
echo.
echo   Health : http://localhost:8000/api/v1/health
echo   Docs   : http://localhost:8000/docs
echo.
echo   Leave this window open. Ctrl+C stops the server.
echo ==================================================
echo.
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
pause
