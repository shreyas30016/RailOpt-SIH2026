@echo off
title Stop RailOpt Server
color 0C

echo ======================================================================
echo    Stopping RailOpt Development Server...
echo ======================================================================
echo.

powershell -Command ^
  "$ports = @(8000, 5500);" ^
  "foreach ($port in $ports) {" ^
  "    $connections = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue;" ^
  "    if ($connections) {" ^
  "        foreach ($conn in $connections) {" ^
  "            $pidToKill = $conn.OwningProcess;" ^
  "            if ($pidToKill -gt 0) {" ^
  "                Write-Host ('[*] Terminating process PID: ' + $pidToKill + ' on port ' + $port);" ^
  "                Stop-Process -Id $pidToKill -Force -ErrorAction SilentlyContinue;" ^
  "            }" ^
  "        }" ^
  "    } else {" ^
  "        Write-Host ('[*] Port ' + $port + ' is free.');" ^
  "    }" ^
  "};" ^
  "Write-Host '[+] RailOpt services stopped successfully!';"

echo.
