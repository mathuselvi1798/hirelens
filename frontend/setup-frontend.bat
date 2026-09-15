@echo off
setlocal
cd /d "%~dp0"

echo ==================================================
echo   Hirelens - frontend setup
echo ==================================================
echo.

where node >nul 2>nul
if errorlevel 1 (
  echo [X] Node.js was not found.
  echo     Install the LTS version from https://nodejs.org then run this again.
  echo.
  pause
  exit /b 1
)

for /f "delims=" %%v in ('node -v') do echo [1/3] Node %%v detected.

echo [2/3] Installing dependencies. The first run takes a few minutes...
call npm install
if errorlevel 1 (
  echo.
  echo [X] npm install failed. Copy the red text above and send it to Claude.
  echo.
  pause
  exit /b 1
)

echo [3/3] Checking types...
call npm run typecheck
if errorlevel 1 (
  echo.
  echo [X] Type check failed. Copy the errors above and send them to Claude.
  echo.
  pause
  exit /b 1
)

echo.
echo ==================================================
echo   Setup complete.
echo   Next: double-click  run-frontend.bat
echo ==================================================
echo.
pause
