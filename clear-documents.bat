@echo off
cd /d "%~dp0backend"
echo Working in: %CD%
echo.
echo Deleting all documents from the Hirelens database...
echo.
".venv\Scripts\python.exe" clear_documents.py
echo.
echo Script finished. If you see an error above, screenshot this whole window.
echo.
pause
