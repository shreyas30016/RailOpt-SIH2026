@echo off
title RailOpt — AI Automatic Block Planning System
color 0B

cd /d "%~dp0\.."

echo ======================================================================
echo   RailOpt: AI Automatic Block Planning System (SIH 2026)
echo ======================================================================
echo.
echo [*] Working Directory: %cd%
echo [*] Target URL:        http://127.0.0.1:8000/login
echo [*] API Documentation: http://127.0.0.1:8000/docs
echo.

set "PYTHON_EXE="

if exist "%cd%\.venv\Scripts\python.exe" (
    echo [+] Using project virtual environment (.venv)...
    set "PYTHON_EXE=%cd%\.venv\Scripts\python.exe"
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
echo Please ensure Python 3.10+ is installed.
pause
exit /b 1

:START_SERVER
echo.
echo [*] Starting RailOpt Server (FastAPI + CP-SAT)...
echo [*] Opening default web browser at http://127.0.0.1:8000/login
start /b "" cmd /c "timeout /t 2 /nobreak >nul & start http://127.0.0.1:8000/login"

%PYTHON_EXE% -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
