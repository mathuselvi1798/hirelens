@echo off
setlocal enabledelayedexpansion
title NEXA AI Analyzer - backend setup
cd /d "%~dp0backend" 2>nul || (echo Could not find the backend folder next to this script. & pause & exit /b 1)

echo ==================================================
echo   NEXA AI Analyzer - backend setup
echo ==================================================
echo.

where python >nul 2>&1
if errorlevel 1 (
  echo [X] Python was not found on your PATH.
  echo     Install Python 3.11+ from python.org, ticking "Add python.exe to PATH".
  pause
  exit /b 1
)
for /f "tokens=2" %%v in ('python -V 2^>^&1') do set PYVER=%%v
echo [1/5] Python !PYVER! detected.

if not exist ".venv\Scripts\python.exe" (
  echo [2/5] Creating virtual environment...
  python -m venv .venv || (echo [X] Could not create the virtual environment. & pause & exit /b 1)
) else (
  echo [2/5] Virtual environment already present.
)
set PY=.venv\Scripts\python.exe

echo [3/5] Installing dependencies. First run takes a few minutes...
"%PY%" -m pip install --upgrade pip --quiet
"%PY%" -m pip install -r requirements.txt
if errorlevel 1 (echo. & echo [X] Dependency install failed - send the output above to Claude. & pause & exit /b 1)

if not exist ".env" (
  echo [4/5] Creating .env from .env.example...
  copy /y ".env.example" ".env" >nul
) else (
  echo [4/5] .env already exists - leaving your settings alone.
)

echo [5/5] Running the test suite...
echo.
"%PY%" -m pytest -q
set TESTRC=!errorlevel!
echo.
if !TESTRC! neq 0 (
  echo ==================================================
  echo   TESTS FAILED - copy the output above to Claude.
  echo ==================================================
) else (
  echo ==================================================
  echo   All tests passed.
  echo   Next: double-click  run-backend.bat
  echo ==================================================
)
echo.
pause
