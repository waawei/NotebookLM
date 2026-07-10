@echo off
chcp 65001 >nul 2>&1
echo ========================================
echo NotebookLM Clone - One-Click Start
echo ========================================
echo.

REM Check backend configuration
if not exist "backend\venv" (
    echo [ERROR] Backend not configured, please run setup.bat first
    pause
    exit /b 1
)

REM Check frontend configuration
if not exist "frontend\node_modules" (
    echo [ERROR] Frontend not configured, please run setup.bat first
    pause
    exit /b 1
)

REM Check API Key
if not exist "backend\.env" (
    echo [ERROR] Backend .env file not found, please run setup.bat first
    pause
    exit /b 1
)

echo Starting frontend and backend services...
echo.
echo ========================================
echo Note:
echo - Backend service: http://localhost:8000
echo - Frontend service: http://localhost:3000
echo - Press Ctrl+C to stop services
echo ========================================
echo.

REM Start backend (in new window)
start "NotebookLM-Backend" cmd /k "cd /d %~dp0backend && call venv\Scripts\activate.bat && python main.py"

REM Wait until backend is actually ready instead of sleeping a fixed time.
echo Waiting for backend health check...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$deadline=(Get-Date).AddSeconds(60); " ^
  "do { " ^
  "  try { $r=Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 'http://127.0.0.1:8000/health'; if ($r.StatusCode -eq 200) { Write-Host 'Backend is ready'; exit 0 } } catch { Start-Sleep -Seconds 1 } " ^
  "} while ((Get-Date) -lt $deadline); " ^
  "Write-Host 'Backend did not become ready at http://127.0.0.1:8000/health within 60 seconds'; exit 1"
if errorlevel 1 (
    echo [ERROR] Backend did not become ready. Check the NotebookLM-Backend window.
    pause
    exit /b 1
)

REM Start frontend (in new window)
start "NotebookLM-Frontend" cmd /k "cd /d %~dp0frontend && npm.cmd run dev"

echo.
echo Two service windows have been started!
echo Browser access: http://localhost:3000
echo.
echo To stop services: Close the corresponding command windows
echo.
pause
