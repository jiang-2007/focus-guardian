@echo off
chcp 65001 >nul
REM ============================================
REM  Focus Guardian - 专注卫士  v2.0.0
REM  一键启动脚本
REM ============================================
REM  首次使用请先安装依赖：
REM      pip install -r requirements.txt
REM ============================================

cd /d "%~dp0"

REM 检查 Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Python，请先安装 Python 3.10+
    echo 下载：https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 检查依赖
python -c "import psutil, win32gui, pystray, PIL" >nul 2>&1
if %errorlevel% neq 0 (
    echo [提示] 缺少依赖，正在自动安装...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [错误] 依赖安装失败，请手动运行：pip install -r requirements.txt
        pause
        exit /b 1
    )
)

REM 启动
echo 🛡️  正在启动 Focus Guardian...
python src\main.py
if %errorlevel% neq 0 pause
