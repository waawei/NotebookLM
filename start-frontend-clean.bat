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
npm cache clean --force
echo Done!
echo.

echo [3/3] Starting Vite dev server...
echo.
echo ================================
echo Frontend will be available at:
echo http://localhost:3000
echo ================================
echo.
npm run dev

pause
