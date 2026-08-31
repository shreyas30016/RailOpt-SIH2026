@echo off
setlocal

title RailOpt - Standalone Frontend UI Server
color 0E

echo ======================================================================
echo    RailOpt - Standalone Frontend UI Server (Port 5500)
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

echo [!] Python was not found in your system PATH!
pause
exit /b 1

:PYTHON_OK
echo [*] Starting lightweight static file server for frontend...
start "RailOpt Static Server" cmd /k "%PYTHON_EXEC% -m http.server 5500 -d frontend"

powershell -Command ^
  "$maxRetries = 15;" ^
  "$ready = $false;" ^
  "for ($i = 1; $i -le $maxRetries; $i++) {" ^
  "    try {" ^
  "        $resp = Invoke-WebRequest -Uri 'http://localhost:5500/dashboard.html' -TimeoutSec 1 -ErrorAction Stop;" ^
  "        if ($resp.StatusCode -eq 200) { $ready = $true; break; }" ^
  "    } catch { Start-Sleep -Milliseconds 400 }" ^
  "};" ^
  "if ($ready) {" ^
  "    Write-Host '[+] Frontend server ready! Opening browser...';" ^
  "    Start-Process 'http://localhost:5500/dashboard.html';" ^
  "} else {" ^
  "    Start-Process 'http://localhost:5500/dashboard.html';" ^
  "}"

echo.
echo ======================================================================
echo   Frontend launched at: http://localhost:5500/dashboard.html
echo ======================================================================
echo.
pause
