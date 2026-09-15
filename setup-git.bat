@echo off
cd /d "%~dp0"
title NEXA - set up version control
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup-git.ps1"
echo.
pause
