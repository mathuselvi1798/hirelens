@echo off
cd /d "%~dp0"
title NEXA - install Google Gemini API key (free tier)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0set-gemini-key.ps1"
echo.
pause
