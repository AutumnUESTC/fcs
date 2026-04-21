"""数据库初始化脚本

运行方式：
    python init_db.py

功能：
    1. 创建数据库（如果不存在）
    2. 创建所有数据表
    3. 创建测试用户（可选）

依赖：
    pip install sqlalchemy pymysql
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import init_db, User, SessionLocal, hash_password


def create_test_users():
    """创建测试用户"""
    db = SessionLocal()
    
    try:
        # 检查是否已有测试用户
        existing = db.query(User).filter(User.username == "test").first()
        if existing:
            print("测试用户已存在，跳过创建")
            return
        
        # 创建测试用户
        test_users = [
            {"username": "test", "password": "123456", "nickname": "测试用户"},
            {"username": "admin", "password": "admin123", "nickname": "管理员"},
        ]
        
        for user_data in test_users:
            user = User(
                username=user_data["username"],
                password_hash=hash_password(user_data["password"]),
                nickname=user_data["nickname"]
            )
            db.add(user)
            print(f"创建用户: {user_data['username']}")
        
        db.commit()
        print("测试用户创建完成")
        
    except Exception as e:
        print(f"创建测试用户失败: {e}")
        db.rollback()
    finally:
        db.close()


def main():
    print("=" * 50)
    print("开始初始化数据库...")
    print("=" * 50)
    
    try:
        # 初始化数据库表
        init_db()
        
        # 创建测试用户
        create_test_users()
        
        print("=" * 50)
        print("数据库初始化完成!")
        print("=" * 50)
        print()
        print("测试用户:")
        print("  用户名: test, 密码: 123456")
        print("  用户名: admin, 密码: admin123")
        print()
        print("环境变量配置:")
        print("  DB_HOST      - 数据库地址 (默认: localhost)")
        print("  DB_PORT      - 数据库端口 (默认: 3306)")
        print("  DB_USER      - 数据库用户 (默认: root)")
        print("  DB_PASSWORD  - 数据库密码 (默认: 123456)")
        print("  DB_NAME      - 数据库名称 (默认: fcs_db)")
        print()
        print("启动后端服务:")
        print("  python app.py")
        print()
        print("启动前端服务:")
        print("  cd fronted_v2 && npm run dev")
        
    except ImportError as e:
        print(f"导入模块失败: {e}")
        print("请确保已安装依赖: pip install sqlalchemy pymysql")
        sys.exit(1)
    except Exception as e:
        print(f"数据库初始化失败: {e}")
        print("请检查:")
        print("  1. MySQL 服务是否运行")
        print("  2. 数据库配置是否正确")
        print("  3. 是否有权限创建数据库")
        sys.exit(1)


if __name__ == "__main__":
    main()
