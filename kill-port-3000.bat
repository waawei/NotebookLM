@echo off
chcp 65001 >nul
echo Killing process on port 3000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000') do (
    echo Found PID: %%a
    taskkill /F /PID %%a
)
echo Done!
pause
