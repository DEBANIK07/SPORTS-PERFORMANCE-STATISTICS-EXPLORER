@echo off
title Sports-Performance Statistics Explorer
cd /d "%~dp0"

echo =========================================================
echo   Sports-Performance Statistics Explorer
echo =========================================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment (.venv) was not found!
    echo Please make sure you run this from inside the project directory.
    echo.
    pause
    exit /b 1
)

echo Starting website server...
start http://127.0.0.1:5000
".venv\Scripts\python.exe" app.py

echo.
echo =========================================================
echo   Server stopped.
echo =========================================================
pause
