@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0run-factoryops-demo.ps1" %*
if errorlevel 1 (
  echo.
  echo SupplyGuard AI demo did not start. See the message above.
  pause
)
endlocal
