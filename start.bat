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
start "NotebookLM-Backend" cmd /k "cd backend && call venv\Scripts\activate.bat && python main.py"

REM Wait 3 seconds for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend (in new window)
start "NotebookLM-Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo Two service windows have been started!
echo Browser access: http://localhost:3000
echo.
echo To stop services: Close the corresponding command windows
echo.
pause
