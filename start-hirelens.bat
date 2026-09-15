@echo off
cd /d "%~dp0"
title Hirelens launcher

echo ==================================================
echo   Starting Hirelens
echo ==================================================
echo.

if not exist "backend\.venv\Scripts\python.exe" (
  echo   [X] Backend is not set up yet.
  echo       Run  backend-setup:  setup-backend.bat
  echo.
  pause
  exit /b 1
)
if not exist "frontend\node_modules" (
  echo   [X] Frontend is not set up yet.
  echo       Run  frontend\setup-frontend.bat
  echo.
  pause
  exit /b 1
)

echo   Opening two windows:
echo     - Hirelens backend   (port 8000)
echo     - Hirelens frontend  (port 3000)
echo.
echo   Keep BOTH open while you use the app.
echo.

start "Hirelens backend" cmd /k "cd /d "%~dp0backend" && .venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000"
start "Hirelens frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo   Waiting for the app to come up...
timeout /t 12 /nobreak >nul
start "" http://localhost:3000

echo.
echo   Browser opened at http://localhost:3000
echo   This launcher window can be closed - the two
echo   server windows must stay open.
echo.
pause
