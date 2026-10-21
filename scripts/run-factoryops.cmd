@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0run-factoryops.ps1"
if errorlevel 1 (
  echo.
  echo SupplyGuard AI 未能启动。请查看上方提示。
  pause
)
endlocal
