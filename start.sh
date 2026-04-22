#!/usr/bin/env bash
set -e

# 颜色
GREEN='\033[92m'
YELLOW='\033[93m'
RED='\033[91m'
CYAN='\033[96m'
RESET='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo "============================================================"
echo -e "       ${GREEN}法脉智联 (FCS) - 一键启动脚本${RESET}"
echo "============================================================"
echo ""

# ----------------------------------------------------------
# 0. 检查 Conda 环境
# ----------------------------------------------------------
echo -e "[1/7] 检查 Conda 环境..."

PYTHON_CMD="python3"
if ! command -v python3 &> /dev/null; then
    PYTHON_CMD="python"
fi

if command -v conda &> /dev/null; then
    echo -e "  ${GREEN}检测到 Conda 已安装!${RESET}"
    echo ""
    echo "  可用的 Conda 环境:"
    echo "  --------------------------------------------------------"
    conda env list 2>/dev/null | grep -v "^#" | while read -r line; do
        env_name=$(echo "$line" | awk '{print $1}')
        env_path=$(echo "$line" | awk '{print $2}')
        if [ -n "$env_name" ]; then
            echo "    $env_name  ($env_path)"
        fi
    done
    echo "  --------------------------------------------------------"
    echo ""
    echo "  [0] 不使用 Conda，使用系统 Python"
    echo ""

    read -p "  请选择 Conda 环境 (输入环境名或序号，0=跳过): " CONDA_CHOICE

    if [ "$CONDA_CHOICE" = "0" ]; then
        echo -e "  ${YELLOW}已跳过 Conda，将使用系统 Python${RESET}"
    else
        echo "  正在激活 Conda 环境: $CONDA_CHOICE"
        eval "$(conda shell.bash hook)"
        conda activate "$CONDA_CHOICE" 2>/dev/null
        if [ $? -ne 0 ]; then
            echo -e "${RED}[错误] 无法激活环境 \"$CONDA_CHOICE\"，请检查环境名是否正确${RESET}"
            exit 1
        fi
        echo -e "  ${GREEN}Conda 环境 \"$CONDA_CHOICE\" 已激活!${RESET}"
        PYTHON_CMD="python"
    fi
else
    echo -e "  ${YELLOW}未检测到 Conda，将使用系统 Python${RESET}"
    echo "  如需使用 Conda，请先安装: https://docs.conda.io/en/latest/miniconda.html"
fi
echo ""

# ----------------------------------------------------------
# 1. 检查环境
# ----------------------------------------------------------
echo -e "[2/7] 检查运行环境..."

if ! command -v $PYTHON_CMD &> /dev/null; then
    echo -e "${RED}[错误] 未找到 Python，请安装 Python 3.10+${RESET}"
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo -e "${RED}[错误] 未找到 Node.js，请安装 Node.js 18+${RESET}"
    exit 1
fi

echo "  Python: $($PYTHON_CMD --version)"
echo "  Node.js: $(node --version)"
echo ""

# ----------------------------------------------------------
# 2. 安装后端依赖
# ----------------------------------------------------------
echo "[3/7] 安装后端 Python 依赖..."
$PYTHON_CMD -m pip install -r requirements.txt -q
echo "  后端依赖安装完成!"
echo ""

# ----------------------------------------------------------
# 3. 安装前端依赖
# ----------------------------------------------------------
echo "[4/7] 安装前端 Node.js 依赖..."
cd "$SCRIPT_DIR/fronted_v2"
if [ ! -d "node_modules" ]; then
    npm install
else
    echo "  前端依赖已存在，跳过安装"
fi
cd "$SCRIPT_DIR"
echo ""

# ----------------------------------------------------------
# 4. 初始化数据库
# ----------------------------------------------------------
echo "[5/7] 初始化数据库..."
$PYTHON_CMD -c "from database import init_db; init_db(); print('  数据库初始化完成!')"

# 确保 is_pinned 列存在
$PYTHON_CMD -c "from database import engine; from sqlalchemy import text; conn=engine.connect(); conn.execute(text('ALTER TABLE conversations ADD COLUMN is_pinned BOOLEAN DEFAULT 0')); conn.commit(); print('  is_pinned 列已添加!')" 2>/dev/null || true
echo ""

# ----------------------------------------------------------
# 5. 启动后端
# ----------------------------------------------------------
echo "[6/7] 启动后端服务 (http://localhost:5000)..."
$PYTHON_CMD app.py &
BACKEND_PID=$!
sleep 3
echo "  后端服务已启动! (PID: $BACKEND_PID)"
echo ""

# ----------------------------------------------------------
# 6. 启动前端
# ----------------------------------------------------------
echo "[7/7] 启动前端服务 (http://localhost:3000)..."
cd "$SCRIPT_DIR/fronted_v2"
npx vite &
FRONTEND_PID=$!
cd "$SCRIPT_DIR"
sleep 3
echo "  前端服务已启动! (PID: $FRONTEND_PID)"
echo ""

# ----------------------------------------------------------
# 完成
# ----------------------------------------------------------
echo "============================================================"
echo -e "  ${GREEN}所有服务已启动!${RESET}"
echo ""
echo "  前端页面: http://localhost:3000"
echo "  后端 API: http://localhost:5000"
echo "  API 文档: http://localhost:5000/docs"
echo ""
echo -e "  ${YELLOW}按 Ctrl+C 停止所有服务${RESET}"
echo "============================================================"
echo ""

# 自动打开浏览器
echo "正在打开浏览器..."
if command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:3000 2>/dev/null &
elif command -v open &> /dev/null; then
    open http://localhost:3000 2>/dev/null &
fi

# 清理函数
cleanup() {
    echo ""
    echo "正在停止所有服务..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    echo "所有服务已停止"
    exit 0
}

trap cleanup SIGINT SIGTERM

# 等待
wait
