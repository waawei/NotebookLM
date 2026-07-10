@echo off
chcp 65001 >nul
echo ================================
echo Starting Frontend (Clean Start)
echo ================================
echo.

echo [1/3] Killing any process on port 3000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000') do (
    echo Found PID: %%a - Killing...
    taskkill /F /PID %%a >nul 2>&1
)
echo Done!
echo.

echo [2/3] Clearing npm cache...
cd frontend
npm.cmd cache clean --force
echo Done!
echo.

echo [3/4] Waiting for backend health check...
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

echo [4/4] Starting Vite dev server...
echo.
echo ================================
echo Frontend will be available at:
echo http://localhost:3000
echo ================================
echo.
npm.cmd run dev

pause
