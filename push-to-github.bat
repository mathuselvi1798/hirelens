@echo off
cd /d "%~dp0"
title NEXA - push to GitHub
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0push-to-github.ps1"
echo.
pause
