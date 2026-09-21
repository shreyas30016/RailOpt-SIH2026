@echo off
title RailOpt Backend Server
color 0A

cd /d "%~dp0"

echo ======================================================================
echo   RailOpt Backend Server (FastAPI + CP-SAT Optimizer)
echo   Host: 127.0.0.1 | Port: 8000
echo ======================================================================
echo.

if exist "%~dp0.venv\Scripts\activate.bat" (
    echo [*] Activating virtual environment (.venv)...
    call "%~dp0.venv\Scripts\activate.bat"
    echo [*] Starting Uvicorn server...
    python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
    goto :DONE
)

py -3 --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [*] Starting Uvicorn with py -3...
    py -3 -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
    goto :DONE
)

echo [*] Starting Uvicorn with system python...
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload

:DONE
if %errorlevel% neq 0 (
    echo.
    echo ======================================================================
    echo [ERROR] Backend server exited with code %errorlevel%.
    echo Check the error messages above.
    echo ======================================================================
    echo.
    pause
)
