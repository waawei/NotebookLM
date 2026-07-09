@echo off
chcp 65001 >nul 2>&1
echo ========================================
echo NotebookLM Clone - One-Click Setup
echo ========================================
echo.
echo This script will automatically configure all dependencies for frontend and backend
echo.

REM Setup backend
echo ---- Setting up Backend ----
cd backend
call setup.bat
cd ..

echo.

REM Setup frontend
echo ---- Setting up Frontend ----
cd frontend
call setup.bat
cd ..

echo.
echo ========================================
echo All setup completed!
echo ========================================
echo.
echo How to start:
echo 1. Run start.bat for one-click startup
echo 2. Or start separately:
echo    - backend\start_backend.bat (Backend)
echo    - frontend\start_frontend.bat (Frontend)
echo.
pause
