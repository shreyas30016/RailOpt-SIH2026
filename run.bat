@echo off
title RailOpt — AI Automatic Block Planning System
color 0B

cd /d "%~dp0"

echo ======================================================================
echo   ==================================================================
echo     RailOpt: AI Automatic Block Planning System (SIH 2026)
echo   ==================================================================
echo ======================================================================
echo.
echo [*] Working Directory: %~dp0
echo [*] Target URL:        http://127.0.0.1:8000/login
echo [*] API Documentation: http://127.0.0.1:8000/docs
echo.

:: 1. Check Python installation & Virtual Environment
set "PYTHON_EXE="

if exist "%~dp0.venv\Scripts\python.exe" (
    echo [+] Using project virtual environment (.venv)...
    set "PYTHON_EXE=%~dp0.venv\Scripts\python.exe"
    goto :START_SERVER
)

where py >nul 2>&1
if %errorlevel% equ 0 (
    echo [+] Using Python launcher (py -3)...
    set "PYTHON_EXE=py -3"
    goto :START_SERVER
)

where python >nul 2>&1
if %errorlevel% equ 0 (
    echo [+] Using system Python...
    set "PYTHON_EXE=python"
    goto :START_SERVER
)

echo.
echo [ERROR] Python was not found on your system or in .venv!
echo Please ensure Python 3.10+ is installed or create a virtual environment:
echo   python -m venv .venv
echo   .venv\Scripts\pip install -r requirements.txt
echo.
pause
exit /b 1

:START_SERVER
echo.
echo ======================================================================
echo [*] Starting RailOpt Backend & Frontend Server (FastAPI + CP-SAT)...
echo [*] Opening default web browser at http://127.0.0.1:8000/login
echo [*] Press CTRL+C to stop the server at any time.
echo ======================================================================
echo.

:: Launch browser in background (using Windows default protocol handler)
start /b "" cmd /c "timeout /t 2 /nobreak >nul & start http://127.0.0.1:8000/login"

:: Start Uvicorn serving both frontend and backend
%PYTHON_EXE% -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload

if %errorlevel% neq 0 (
    echo.
    echo ======================================================================
    echo [ERROR] RailOpt server stopped with exit code %errorlevel%.
    echo ======================================================================
    echo.
    pause
)
