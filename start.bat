@echo off
setlocal enabledelayedexpansion

title RailOpt - Indian Railways Block Planning System
color 0B

echo ======================================================================
echo    RAILOPT: AI-Powered Automatic Block Planning for Indian Railways
echo             SIH 2026 Problem Statement SIH26027
echo ======================================================================
echo.

cd /d "%~dp0"

REM 1. Detect Python
set "PYTHON_EXEC="
py -3 --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_EXEC=py -3"
    goto :PYTHON_OK
)

python --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_EXEC=python"
    goto :PYTHON_OK
)

echo [!] ERROR: Python 3 is not installed or not in your system PATH!
echo [*] Please install Python 3.10+ from https://www.python.org/
echo.
pause
exit /b 1

:PYTHON_OK
echo [*] Detected Python environment: %PYTHON_EXEC%

REM 2. Free Port 8000 if occupied
echo [*] Checking port 8000 availability...
powershell -Command ^
  "$conn = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue;" ^
  "if ($conn) {" ^
  "    foreach ($c in $conn) {" ^
  "        $p = $c.OwningProcess;" ^
  "        if ($p -gt 0) {" ^
  "            Write-Host ('[*] Freeing occupied port 8000 (PID: ' + $p + ')...');" ^
  "            Stop-Process -Id $p -Force -ErrorAction SilentlyContinue;" ^
  "        }" ^
  "    }" ^
  "}"

REM 3. Check for .env file
if not exist ".env" (
    if exist ".env.example" (
        echo [*] Initializing .env from .env.example...
        copy ".env.example" ".env" >nul
    )
)

REM 4. Verify Dependencies
echo [*] Verifying backend dependencies...
%PYTHON_EXEC% -c "import fastapi, uvicorn, ortools, sqlalchemy, pydantic, httpx" >nul 2>&1
if %errorlevel% neq 0 (
    echo [*] Installing required packages from requirements.txt...
    %PYTHON_EXEC% -m pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [!] Failed to install dependencies. Check your network or pip setup.
        pause
        exit /b 1
    )
)
echo [*] Dependencies verified.
echo.

REM 5. Check Frontend Entrypoint
if not exist "frontend\dashboard.html" (
    echo [!] WARNING: frontend\dashboard.html not found!
) else (
    if not exist "frontend\index.html" (
        copy "frontend\dashboard.html" "frontend\index.html" >nul
    )
)

REM 6. Start Backend Server in background and poll for readiness
echo [*] Starting RailOpt Full-Stack Engine (FastAPI + OR-Tools Optimizer)...
start "RailOpt Backend Server" cmd /k "%PYTHON_EXEC% -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload"

echo [*] Waiting for server to become healthy on http://127.0.0.1:8000/health...

REM 7. Active Health-Check Polling and Browser Launch
powershell -Command ^
  "$maxRetries = 20;" ^
  "$ready = $false;" ^
  "for ($i = 1; $i -le $maxRetries; $i++) {" ^
  "    try {" ^
  "        $resp = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/health' -TimeoutSec 1 -ErrorAction Stop;" ^
  "        if ($resp.status -eq 'healthy') { $ready = $true; break; }" ^
  "    } catch { Start-Sleep -Milliseconds 600 }" ^
  "};" ^
  "if ($ready) {" ^
  "    Write-Host '[+] Server is ready! Launching default browser to Dashboard...';" ^
  "    Start-Process 'http://127.0.0.1:8000/dashboard';" ^
  "} else {" ^
  "    Write-Host '[!] Server start timed out. You can manually visit http://127.0.0.1:8000/dashboard';" ^
  "}"

echo.
echo ======================================================================
echo   RailOpt is running at:
echo   - Operations Dashboard:     http://127.0.0.1:8000/dashboard
echo   - Maintenance Requests:     http://127.0.0.1:8000/maintenance-requests
echo   - Block Planning:           http://127.0.0.1:8000/block-planning
echo   - Gantt Timeline View:      http://127.0.0.1:8000/gantt-view
echo   - What-If Scenario Sim:     http://127.0.0.1:8000/what-if
echo   - Interactive API Docs:     http://127.0.0.1:8000/docs
echo ======================================================================
echo [*] Run 'stop.bat' or close the backend terminal to stop the server.
echo.
pause
