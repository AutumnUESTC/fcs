"""
数据库配置模块
提供 MySQL 数据库连接和初始化功能
"""

import os
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import text
from datetime import datetime

# 数据库配置（从环境变量读取或使用默认值）
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "123456")
DB_NAME = os.getenv("DB_NAME", "fcs_db")

# 构建数据库 URL
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

# 创建引擎
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()


# ==============================================================================
# 数据库模型
# ==============================================================================

class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    nickname = Column(String(100), default="")
    email = Column(String(100), default="")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    is_active = Column(Boolean, default=True)

    # 关系
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")


class Conversation(Base):
    """会话表"""
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(String(100), unique=True, nullable=False, index=True)  # 前端使用的 UUID
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    service_id = Column(String(50), default="qa")  # 服务类型
    title = Column(String(255), default="新对话")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关系
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    """消息表"""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    role = Column(String(20), nullable=False)  # user / assistant
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    # 关系
    conversation = relationship("Conversation", back_populates="messages")


class LegalAnalysis(Base):
    """法律分析记录表"""
    __tablename__ = "legal_analyses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(100), nullable=False, index=True)  # 分析会话ID
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user_input = Column(Text, nullable=False)  # 用户输入
    intent = Column(Text)  # 提取的意图
    report_content = Column(Text)  # 分析报告
    status = Column(String(20), default="completed")  # completed / need_info / error
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


# ==============================================================================
# 数据库操作函数
# ==============================================================================

def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化数据库，创建所有表"""
    # 先创建数据库（如果不存在）
    temp_url = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/?charset=utf8mb4"
    temp_engine = create_engine(temp_url)
    
    with temp_engine.connect() as conn:
        conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
        conn.commit()
    
    temp_engine.dispose()
    
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    print(f"数据库 {DB_NAME} 初始化完成")


def drop_db():
    """删除所有表（仅用于测试）"""
    Base.metadata.drop_all(bind=engine)
    print("数据库表已删除")
