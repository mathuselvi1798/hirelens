@echo off
REM Right-click this file and choose "Run as administrator".
REM It resets the forgotten postgres password and creates the hirelens database.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0reset-postgres-password.ps1"
echo.
pause
