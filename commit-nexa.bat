@echo off
cd /d "%~dp0"
title NEXA - commit to version control
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0commit-nexa.ps1"
echo.
pause
