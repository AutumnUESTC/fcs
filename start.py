"""
前后端一键启动脚本

功能：
    1. 初始化数据库
    2. 启动后端服务 (FastAPI)
    3. 启动前端服务 (Vite dev server)

使用方式：
    python start.py

依赖：
    后端: pip install fastapi uvicorn sqlalchemy pymysql
    前端: cd fronted_v2 && npm install
"""

import sys
import os
import subprocess
import time
import signal

# 颜色输出
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[0m'


def print_info(msg):
    print(f"{GREEN}[INFO]{RESET} {msg}")


def print_warn(msg):
    print(f"{YELLOW}[WARN]{RESET} {msg}")


def print_error(msg):
    print(f"{RED}[ERROR]{RESET} {msg}")


def init_database():
    """初始化数据库"""
    print_info("检查并初始化数据库...")
    
    try:
        from database import init_db
        init_db()
        print_info("数据库初始化完成!")
        return True
    except ImportError as e:
        print_error(f"导入数据库模块失败: {e}")
        print_error("请确保已安装依赖: pip install sqlalchemy pymysql")
        return False
    except Exception as e:
        print_error(f"数据库初始化失败: {e}")
        print_error("请检查 MySQL 服务是否运行，以及数据库配置是否正确")
        return False


def start_backend():
    """启动后端服务"""
    print_info("启动后端服务 (http://localhost:8000)...")
    
    try:
        # 使用 subprocess.Popen 启动后端，不使用 shell=True
        proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        
        # 等待后端启动
        time.sleep(3)
        
        if proc.poll() is not None:
            print_error("后端服务启动失败")
            return None
        
        print_info("后端服务已启动!")
        return proc
        
    except Exception as e:
        print_error(f"启动后端失败: {e}")
        return None


def start_frontend():
    """启动前端服务"""
    frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fronted_v2")
    
    if not os.path.exists(frontend_dir):
        print_error(f"前端目录不存在: {frontend_dir}")
        return None
    
    print_info("启动前端服务 (http://localhost:3000)...")
    
    try:
        proc = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=frontend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        
        # 等待前端启动
        time.sleep(5)
        
        if proc.poll() is not None:
            print_error("前端服务启动失败")
            return None
        
        print_info("前端服务已启动!")
        return proc
        
    except Exception as e:
        print_error(f"启动前端失败: {e}")
        print_error("请确保已安装 Node.js 和 npm")
        return None


def main():
    print()
    print("=" * 60)
    print(f"{GREEN}        智法精灵 - 前后端一键启动{RESET}")
    print("=" * 60)
    print()
    
    processes = []
    
    try:
        # 1. 初始化数据库
        if not init_database():
            print_error("数据库初始化失败，退出")
            sys.exit(1)
        
        print()
        
        # 2. 启动后端
        backend_proc = start_backend()
        if backend_proc:
            processes.append(backend_proc)
        else:
            print_warn("后端启动失败，继续启动前端...")
        
        print()
        
        # 3. 启动前端
        frontend_proc = start_frontend()
        if frontend_proc:
            processes.append(frontend_proc)
        else:
            print_warn("前端启动失败")
        
        print()
        print("=" * 60)
        print(f"{GREEN}服务已启动!{RESET}")
        print(f"  后端 API: {GREEN}http://localhost:8000{RESET}")
        print(f"  前端页面: {GREEN}http://localhost:3000{RESET}")
        print(f"  API 文档: {GREEN}http://localhost:8000/docs{RESET}")
        print()
        print(f"{YELLOW}按 Ctrl+C 停止所有服务{RESET}")
        print("=" * 60)
        print()
        
        # 等待所有进程
        while True:
            for proc in processes:
                if proc.poll() is not None:
                    print_warn("某个服务已停止")
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        print()
        print_info("正在停止所有服务...")
        
    finally:
        # 停止所有进程
        for proc in processes:
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except Exception:
                proc.kill()
        
        print_info("所有服务已停止")
        print_info("再见!")


if __name__ == "__main__":
    main()
