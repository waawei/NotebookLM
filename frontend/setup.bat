@echo off
chcp 65001 >nul 2>&1
echo ========================================
echo NotebookLM Clone - Frontend Auto Setup
echo ========================================
echo.

REM Check Node.js installation
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found, please install Node.js 18+
    echo Download: https://nodejs.org/
    pause
    exit /b 1
)

echo [1/3] Checking Node.js version...
node --version
npm --version
echo.

REM Install dependencies
echo [2/3] Installing frontend dependencies...
echo This may take a few minutes, please wait...
echo.

npm install --registry=https://registry.npmmirror.com
if errorlevel 1 (
    echo [WARNING] Installation failed with npmmirror, trying official source...
    npm install
)

if errorlevel 1 (
    echo [ERROR] Dependencies installation failed
    pause
    exit /b 1
)

echo.
echo Dependencies installed successfully!
echo.

echo [3/3] Verifying installation...
if exist "node_modules" (
    echo node_modules directory created
) else (
    echo [WARNING] node_modules directory not found
)
echo.

echo ========================================
echo Frontend setup completed!
echo ========================================
echo.
echo Next step:
echo Run start_frontend.bat to start the frontend service
echo.
pause
