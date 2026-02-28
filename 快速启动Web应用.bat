@echo off
title GraphRAG Web应用快速启动器
echo.
echo ========================================
echo   GraphRAG Web应用快速启动器
echo   计算机网络知识图谱问答系统
echo ========================================
echo.

echo 正在启动Web应用，请稍候...
echo.

REM 切换到脚本所在目录
cd /d "%~dp0"

REM 使用快速启动脚本
python fast_start_web_app.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo 启动失败，请检查错误信息
    pause
    exit /b 1
)

pause