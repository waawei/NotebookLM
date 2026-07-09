@echo off
chcp 65001 >nul 2>&1
echo ========================================
echo NotebookLM Clone - Backend Auto Setup
echo ========================================
echo.

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found, please install Python 3.10+
    echo Download: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/6] Checking Python version...
python --version
echo.

REM Create virtual environment
echo [2/6] Creating Python virtual environment...
if not exist "venv" (
    python -m venv venv
    echo Virtual environment created successfully!
) else (
    echo Virtual environment already exists, skipping creation
)
echo.

REM Activate virtual environment
echo [3/6] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)
echo Virtual environment activated
echo.

REM Install dependencies
echo [4/6] Installing Python dependencies...
echo This may take a few minutes, please wait...
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
if errorlevel 1 (
    echo [WARNING] Installation failed with Tsinghua mirror, trying official source...
    pip install -r requirements.txt
)
echo Dependencies installed successfully!
echo.

REM Create necessary directories
echo [5/6] Creating data directories...
if not exist "data" mkdir data
if not exist "data\uploads" mkdir data\uploads
if not exist "data\chroma_db" mkdir data\chroma_db
echo Data directories created!
echo.

REM Copy config file
echo [6/6] Setting up environment variables...
if not exist ".env" (
    copy .env.example .env >nul
    echo .env file created
    echo.
    echo ========================================
    echo [IMPORTANT] Please edit .env file and fill in your API Key
    echo ========================================
    echo.
    echo 1. Open backend\.env file
    echo 2. Change LLM_API_KEY=your_api_key_here to your real API Key
    echo.
    echo Get API Key (Recommended: Qwen):
    echo - Qwen: https://dashscope.console.aliyun.com/
    echo - OpenAI: https://platform.openai.com/
    echo.
    notepad .env
) else (
    echo .env file already exists
)
echo.

echo ========================================
echo Backend setup completed!
echo ========================================
echo.
echo Next steps:
echo 1. Make sure .env file has your API Key configured
echo 2. Run start_backend.bat to start the backend service
echo.
pause
