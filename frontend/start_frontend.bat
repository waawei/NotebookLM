@echo off
chcp 65001 >nul 2>&1
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

echo [1/1] Starting Vite development server...
echo.
echo ========================================
echo Frontend service is running...
echo Access URL: http://localhost:3000
echo ========================================
echo.
echo Press Ctrl+C to stop the service
echo.

npm run dev

pause
