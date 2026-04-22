@echo off
chcp 65001 >nul 2>&1
title 法脉智联 - 一键启动

echo.
echo ============================================================
echo          法脉智联 (FCS) - 一键启动脚本
echo ============================================================
echo.

:: ----------------------------------------------------------
:: 0. 检查 Conda 环境
:: ----------------------------------------------------------
echo [1/7] 检查 Conda 环境...

set "CONDA_FOUND=0"
where conda >nul 2>&1
if %errorlevel% equ 0 set "CONDA_FOUND=1"

if "%CONDA_FOUND%"=="1" (
    echo   检测到 Conda 已安装!
    echo.
    echo   可用的 Conda 环境:
    echo   --------------------------------------------------------
    conda env list 2>nul
    echo   --------------------------------------------------------
    echo.
    echo   [0] 不使用 Conda，使用系统 Python
    echo.
    set /p "CONDA_CHOICE=  请选择 Conda 环境 (输入环境名或序号，0=跳过): "

    if "%CONDA_CHOICE%"=="0" (
        echo   已跳过 Conda，将使用系统 Python
    ) else (
        echo   正在激活 Conda 环境: %CONDA_CHOICE%
        call conda activate %CONDA_CHOICE% 2>nul
        if %errorlevel% neq 0 (
            echo   [错误] 无法激活环境 "%CONDA_CHOICE%"，请检查环境名是否正确
            pause
            exit /b 1
        )
        echo   Conda 环境 "%CONDA_CHOICE%" 已激活!
    )
) else (
    echo   未检测到 Conda，将使用系统 Python
    echo   如需使用 Conda，请先安装: https://docs.conda.io/en/latest/miniconda.html
)
echo.

:: ----------------------------------------------------------
:: 1. 检查 Python 和 Node.js
:: ----------------------------------------------------------
echo [2/7] 检查运行环境...

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Python，请安装 Python 3.10+ 并加入 PATH
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Node.js，请安装 Node.js 18+ 并加入 PATH
    echo 下载地址: https://nodejs.org/
    pause
    exit /b 1
)

echo   Python: 
python --version
echo   Node.js: 
node --version
echo.

:: ----------------------------------------------------------
:: 2. 安装后端 Python 依赖
:: ----------------------------------------------------------
echo [3/7] 安装后端 Python 依赖...
pip install -r requirements.txt -q
if %errorlevel% neq 0 (
    echo [错误] 后端依赖安装失败，请检查网络连接
    pause
    exit /b 1
)
echo   后端依赖安装完成!
echo.

:: ----------------------------------------------------------
:: 3. 安装前端 Node.js 依赖
:: ----------------------------------------------------------
echo [4/7] 安装前端 Node.js 依赖...
cd /d "%~dp0fronted_v2"
if not exist node_modules (
    call npm install
    if %errorlevel% neq 0 (
        echo [错误] 前端依赖安装失败，请检查网络连接
        cd /d "%~dp0"
        pause
        exit /b 1
    )
) else (
    echo   前端依赖已存在，跳过安装
)
cd /d "%~dp0"
echo.

:: ----------------------------------------------------------
:: 4. 初始化数据库 & 数据库迁移
:: ----------------------------------------------------------
echo [5/7] 初始化数据库...
python -c "from database import init_db; init_db(); print('  数据库初始化完成!')"
if %errorlevel% neq 0 (
    echo [错误] 数据库初始化失败
    pause
    exit /b 1
)

:: 确保 is_pinned 列存在（兼容旧数据库）
python -c "from database import engine; from sqlalchemy import text; conn=engine.connect(); conn.execute(text('ALTER TABLE conversations ADD COLUMN is_pinned BOOLEAN DEFAULT 0')); conn.commit(); print('  is_pinned 列已添加!')" >nul 2>&1
echo.

:: ----------------------------------------------------------
:: 5. 启动后端
:: ----------------------------------------------------------
echo [6/7] 启动后端服务 (http://localhost:5000)...
start "FCS-后端" cmd /c "python app.py"
timeout /t 3 /nobreak >nul
echo   后端服务已启动!
echo.

:: ----------------------------------------------------------
:: 6. 启动前端
:: ----------------------------------------------------------
echo [7/7] 启动前端服务 (http://localhost:3000)...
cd /d "%~dp0fronted_v2"
start "FCS-前端" cmd /c "npx vite"
cd /d "%~dp0"
echo   前端服务已启动!
echo.

:: ----------------------------------------------------------
:: 完成
:: ----------------------------------------------------------
echo ============================================================
echo   所有服务已启动!
echo.
echo   前端页面: http://localhost:3000
echo   后端 API: http://localhost:5000
echo   API 文档: http://localhost:5000/docs
echo.
echo   关闭此窗口或按 Ctrl+C 不会停止服务
echo   请手动关闭 "FCS-后端" 和 "FCS-前端" 窗口来停止服务
echo ============================================================
echo.

:: 自动打开浏览器
echo 正在打开浏览器...
start http://localhost:3000

pause
