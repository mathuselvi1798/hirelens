@echo off
setlocal
cd /d "%~dp0"
title NEXA - install API key

echo ==================================================
echo   NEXA - install your Anthropic API key
echo ==================================================
echo.
echo   1. Go to console.anthropic.com  -  API keys
echo   2. Create a key, then click "Copy key"
echo   3. Come back to this window
echo   4. RIGHT-CLICK once to paste, then press Enter
echo.
echo   Nothing is sent anywhere. The key is written only
echo   to backend\.env on this computer.
echo.

set "NEXA_KEY="
set /p "NEXA_KEY=Paste your API key here: "

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0set-api-key.ps1"

echo.
pause
