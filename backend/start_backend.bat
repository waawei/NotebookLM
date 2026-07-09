@echo off
chcp 65001 >nul 2>&1
echo ========================================
echo NotebookLM Clone - Backend Service Start
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo [ERROR] Virtual environment not found!
    echo Please run setup.bat first
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist ".env" (
    echo [ERROR] .env config file not found!
    echo Please run setup.bat first
    pause
    exit /b 1
)

REM Activate virtual environment
echo [1/2] Activating virtual environment...
call venv\Scripts\activate.bat
echo.

REM Start service
echo [2/2] Starting FastAPI service...
echo.
echo ========================================
echo Backend service is running...
echo API URL: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo ========================================
echo.
echo Press Ctrl+C to stop the service
echo.

python main.py

pause
