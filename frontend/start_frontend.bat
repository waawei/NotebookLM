@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"
echo ========================================
echo NotebookLM Clone - Frontend Service Start
echo ========================================
echo.

REM Check if node_modules exists
if not exist "node_modules" (
    echo [ERROR] Dependencies not installed!
    echo Please run setup.bat first
    pause
    exit /b 1
)

echo [1/2] Waiting for backend health check...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$deadline=(Get-Date).AddSeconds(60); " ^
  "do { " ^
  "  try { $r=Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 'http://127.0.0.1:8000/health'; if ($r.StatusCode -eq 200) { Write-Host 'Backend is ready'; exit 0 } } catch { Start-Sleep -Seconds 1 } " ^
  "} while ((Get-Date) -lt $deadline); " ^
  "Write-Host 'Backend did not become ready at http://127.0.0.1:8000/health within 60 seconds'; exit 1"
if errorlevel 1 (
    echo [ERROR] Backend is not ready. Start backend\start_backend.bat first.
    pause
    exit /b 1
)
echo.

echo [2/2] Starting Vite development server...
echo.
echo ========================================
echo Frontend service is running...
echo Access URL: http://localhost:3000
echo ========================================
echo.
echo Press Ctrl+C to stop the service
echo.

npm.cmd run dev

pause
