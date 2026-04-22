"""
用户认证模块
提供用户注册、登录、Token 生成等功能
"""

import os
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import User, get_db

# JWT 密钥（生产环境应从环境变量读取）
SECRET_KEY = os.getenv("FCS_SECRET_KEY", "your-secret-key-change-in-production-12345")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

# 简单的 Token 方案（不依赖外部库）
security = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    """密码哈希（使用 SHA256 + salt）"""
    salt = SECRET_KEY[:16]
    pwd_hash = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
    return f"{salt}${pwd_hash}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    if "$" not in hashed_password:
        return False
    salt, stored_hash = hashed_password.split("$", 1)
    pwd_hash = hashlib.sha256(f"{salt}{plain_password}".encode()).hexdigest()
    return secrets.compare_digest(pwd_hash, stored_hash)


# 向后兼容别名
password_hash = property(lambda self: self.password)


def create_access_token(user_id: int, username: str) -> str:
    """创建访问令牌（使用 | 分隔符避免与时间戳冒号冲突）"""
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    payload = f"{user_id}|{username}|{expire.isoformat()}"
    signature = hashlib.sha256(f"{SECRET_KEY}{payload}".encode()).hexdigest()
    return f"{payload}|{signature}"


def verify_access_token(token: str) -> Optional[dict]:
    """验证访问令牌"""
    try:
        # Token格式: user_id|username|iso_timestamp|signature
        parts = token.split('|')
        if len(parts) != 4:
            return None
        
        user_id_str, username, expire_str, signature = parts
        
        # 验证签名
        payload = f"{user_id_str}|{username}|{expire_str}"
        expected_sig = hashlib.sha256(f"{SECRET_KEY}{payload}".encode()).hexdigest()
        
        if not secrets.compare_digest(signature, expected_sig):
            return None
        
        # 检查过期
        expire = datetime.fromisoformat(expire_str)
        if expire < datetime.utcnow():
            return None
        
        return {"user_id": int(user_id_str), "username": username}
    except Exception:
        return None


# ==============================================================================
# Pydantic 模型
# ==============================================================================

class TokenData(BaseModel):
    """Token 数据"""
    user_id: int
    username: str


class RegisterRequest(BaseModel):
    """注册请求"""
    username: str
    password: str
    nickname: Optional[str] = ""


class LoginRequest(BaseModel):
    """登录请求"""
    username: str
    password: str


class UserResponse(BaseModel):
    """用户响应"""
    id: int
    username: str
    nickname: str
    email: Optional[str] = None

    class Config:
        from_attributes = True


# ==============================================================================
# 依赖项
# ==============================================================================

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
) -> User:
    """获取当前登录用户（支持 Bearer Token 或 X-User-Id Header）"""
    user = None
    
    # 方式1: Bearer Token
    if credentials:
        token_data = verify_access_token(credentials.credentials)
        if token_data:
            user = db.query(User).filter(User.id == token_data["user_id"]).first()
    
    # 方式2: X-User-Id Header（简化方式，适合开发/测试）
    elif x_user_id:
        try:
            user_id = int(x_user_id)
            user = db.query(User).filter(User.id == user_id).first()
        except ValueError:
            pass
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未认证，请先登录",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用",
        )
    
    return user


def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
) -> Optional[User]:
    """获取当前用户（可选，未登录返回 None）"""
    try:
        return get_current_user(credentials, db, x_user_id)
    except HTTPException:
        return None
