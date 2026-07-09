@echo off
chcp 65001 >nul
echo ========================================
echo 🧪 NotebookLM Clone - P0 功能测试
echo ========================================
echo.

echo 📋 测试清单：
echo    1. 引用编号系统 [1], [2], [3]
echo    2. 建议问题生成
echo    3. 文档摘要生成
echo    4. 对话历史持久化
echo.

echo ⏳ 等待后端启动（10秒）...
timeout /t 10 /nobreak >nul

echo.
echo 🚀 开始测试...
echo.

cd /d "%~dp0"
python test_p0_features.py

echo.
pause
