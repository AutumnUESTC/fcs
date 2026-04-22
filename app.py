"""法律多智能体系统 - FastAPI 服务入口

提供 HTTP 接口触发主控工作流执行，支持多轮对话和文件上传。

接口：
  POST /api/legal/analyze   — 提交法律问题（首次请求或用户回复）
  POST /api/legal/upload    — 上传文件，返回服务器路径供 analyze 使用
  GET  /api/legal/health    — 健康检查
  POST /api/auth/register   — 用户注册
  POST /api/auth/login       — 用户登录
  GET  /api/conversations    — 获取会话列表
  GET  /api/conversations/:id — 获取会话详情
  POST /api/conversations    — 保存会话
  POST /api/messages         — 发送消息

多轮对话流程：
  1. 客户端发送首次请求（user_input）
  2. 如果系统需要更多信息，返回 status="need_info" + pending_question
  3. 客户端发送回复（session_id + user_response）
  4. 重复 2-3 直到信息完整，系统返回 status="completed" + 报告

==========================================================================
前后端对接说明
==========================================================================

【后端接口】

1. POST /api/auth/register
   - Content-Type: application/json
   - 参数: {"username": "xxx", "password": "xxx", "nickname": "xxx"}
   - 返回: {"code": 200, "message": "success", "data": {"id": 1, "username": "xxx", "nickname": "xxx"}}

2. POST /api/auth/login
   - Content-Type: application/json
   - 参数: {"username": "xxx", "password": "xxx"}
   - 返回: {"code": 200, "message": "success", "data": {"token": "xxx", "user": {...}}}

3. POST /api/legal/upload
   - Content-Type: multipart/form-data
   - 参数: files (可多个文件)
   - 返回: {"file_paths": ["uploads/xxx.pdf", ...]}
   - 文件保存到项目根目录的 uploads/ 文件夹

4. POST /api/legal/analyze
   - Content-Type: application/json
   - 参数:
     {
       "user_input": "用户的法律问题",
       "uploaded_files": ["uploads/xxx.pdf"],
       "session_id": "",
       "user_response": ""
     }
   - 返回:
     - status="need_info":  需要追问，前端展示 pending_question 并让用户回复
     - status="completed":  完成，前端展示 report_content
     - status="error":      出错，前端展示 steps 中的调试信息

5. GET /api/conversations
   - 获取用户的会话列表
   - 需要认证（Header: Authorization: Bearer <token> 或 X-User-Id: <user_id>）

6. GET /api/conversations/:id
   - 获取会话详情（包含消息）
   - 需要认证

7. POST /api/conversations
   - 创建或更新会话
   - 需要认证

8. POST /api/messages
   - 发送消息（触发法律分析）
   - 需要认证

==========================================================================
"""

from __future__ import annotations

import asyncio
import logging
import os
import shutil
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, status, Header, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import text

from agents.main_graph import main_graph
from agents.states import GlobalCaseState
from database import (
    Base, engine, get_db, init_db,
    User, Conversation, Message, LegalAnalysis
)
from auth import (
    hash_password, verify_password, create_access_token,
    RegisterRequest, LoginRequest, UserResponse, get_current_user, get_current_user_optional
)

# 日志目录：项目根目录下的 logs/
_LOG_DIR = Path(__file__).parent / "logs"
_LOG_DIR.mkdir(exist_ok=True)

# 文件上传目录：项目根目录下的 uploads/
_UPLOAD_DIR = Path(__file__).parent / "uploads"
_UPLOAD_DIR.mkdir(exist_ok=True)

from datetime import datetime

_log_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(_LOG_DIR / f"fcs_{_log_timestamp}.log", encoding="utf-8"),
    ],
)

_file_debug_handler = logging.FileHandler(_LOG_DIR / f"fcs_debug_{_log_timestamp}.log", encoding="utf-8")
_file_debug_handler.setLevel(logging.DEBUG)
_file_debug_handler.setFormatter(logging.Formatter("%(asctime)s [%(name)s] %(message)s"))
logging.getLogger("agents").addHandler(_file_debug_handler)
logging.getLogger("agents").setLevel(logging.DEBUG)
logger = logging.getLogger("fcs.server")

_WORKFLOW_TIMEOUT = int(os.getenv("FCS_WORKFLOW_TIMEOUT", "600"))

# 会话存储：内存缓存，用于多轮对话续传
_session_store: dict[str, dict[str, Any]] = {}


# ---------------------------------------------------------------------------
# 通用响应模型
# ---------------------------------------------------------------------------

class ApiResponse(BaseModel):
    """通用 API 响应"""
    code: int = 200
    message: str = "success"
    data: Any = None


# ---------------------------------------------------------------------------
# 请求 / 响应模型
# ---------------------------------------------------------------------------

class AnalyzeRequest(BaseModel):
    """法律分析请求"""
    user_input: str = Field(default="", description="用户的法律问题或诉求描述")
    uploaded_files: list[str] = Field(default_factory=list, description="上传文件路径列表")
    session_id: str = Field(default="", description="会话ID")
    user_response: str = Field(default="", description="用户对追问的回复")


class AnalyzeResponse(BaseModel):
    """法律分析响应"""
    success: bool
    status: str = "completed"
    session_id: str = ""

    pending_question: str = ""
    missing_info: list[str] = []

    intent: dict[str, Any] | None = None
    execution_results: list[dict[str, Any]] = []
    report_content: str | None = None
    review_passed: bool | None = None
    review_issues: list[str] = []

    user_emotion: dict[str, Any] | None = None
    steps: list[dict[str, Any]] = []


class UploadResponse(BaseModel):
    """文件上传响应"""
    success: bool
    file_paths: list[str] = Field(default_factory=list)
    error: str = ""


# ---------------------------------------------------------------------------
# 会话 API 模型
# ---------------------------------------------------------------------------

class ConversationCreate(BaseModel):
    """创建会话请求"""
    conversation_id: str
    service_id: str = "qa"


class MessageCreate(BaseModel):
    """发送消息请求"""
    conversation_id: str
    content: str
    role: str = "user"


class ConversationResponse(BaseModel):
    """会话响应"""
    id: int
    conversation_id: str
    service_id: str
    title: str
    created_at: str
    updated_at: str


class ConversationDetailResponse(BaseModel):
    """会话详情响应"""
    id: int
    conversation_id: str
    service_id: str
    title: str
    created_at: str
    updated_at: str
    messages: list[dict] = []


# ---------------------------------------------------------------------------
# 应用生命周期
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化数据库
    logger.info("正在初始化数据库...")
    try:
        init_db()
        logger.info("数据库初始化完成")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
    logger.info("法律多智能体系统服务启动")
    yield
    logger.info("法律多智能体系统服务关闭")


app = FastAPI(
    title="法律多智能体系统 (FCS)",
    description="基于 LangGraph 的法律多智能体系统，支持多轮对话、合同审查、法规查询等",
    version="2.0.0",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# 用户认证接口
# ---------------------------------------------------------------------------

@app.post("/api/auth/register", response_model=ApiResponse)
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """用户注册"""
    # 检查用户名是否已存在
    existing = db.query(User).filter(User.username == request.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    # 创建用户
    user = User(
        username=request.username,
        password=hash_password(request.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    logger.info(f"新用户注册: {user.username}")
    
    return ApiResponse(
        code=200,
        message="注册成功",
        data={
            "id": user.id,
            "username": user.username
        }
    )


@app.post("/api/auth/login", response_model=ApiResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """用户登录"""
    user = db.query(User).filter(User.username == request.username).first()
    
    if not user or not verify_password(request.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )
    
    # 生成 Token
    token = create_access_token(user.id, user.username)
    
    logger.info(f"用户登录: {user.username}")
    
    return ApiResponse(
        code=200,
        message="登录成功",
        data={
            "token": token,
            "user": {
                "id": user.id,
                "username": user.username,
                "nickname": user.nickname
            }
        }
    )


@app.get("/api/auth/me", response_model=ApiResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return ApiResponse(
        code=200,
        message="success",
        data={
            "id": current_user.id,
            "username": current_user.username,
            "nickname": current_user.nickname,
            "email": current_user.email
        }
    )


# ---------------------------------------------------------------------------
# 会话管理接口
# ---------------------------------------------------------------------------

@app.get("/api/conversations", response_model=ApiResponse)
async def get_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户的会话列表"""
    conversations = db.query(Conversation).filter(
        Conversation.user_id == current_user.id
    ).order_by(Conversation.updated_at.desc()).all()
    
    return ApiResponse(
        code=200,
        message="success",
        data=[
            {
                "id": conv.id,
                "conversation_id": conv.conversation_id,
                "service_id": conv.service_id,
                "title": conv.title,
                "created_at": conv.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "updated_at": conv.updated_at.strftime("%Y-%m-%d %H:%M:%S")
            }
            for conv in conversations
        ]
    )


@app.get("/api/conversations/{conversation_id}", response_model=ApiResponse)
async def get_conversation_detail(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取会话详情"""
    conversation = db.query(Conversation).filter(
        Conversation.conversation_id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )
    
    # 获取消息（使用 session_id 查询）
    messages = db.query(Message).filter(
        Message.session_id == conversation.conversation_id
    ).order_by(Message.created_at.asc()).all()
    
    return ApiResponse(
        code=200,
        message="success",
        data={
            "id": conversation.id,
            "conversation_id": conversation.conversation_id,
            "service_id": conversation.service_id,
            "title": conversation.title,
            "created_at": conversation.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": conversation.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content
                }
                for msg in messages
            ]
        }
    )


@app.post("/api/conversations", response_model=ApiResponse)
async def create_or_update_conversation(
    request: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建或更新会话"""
    conversation = db.query(Conversation).filter(
        Conversation.conversation_id == request.conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        conversation = Conversation(
            conversation_id=request.conversation_id,
            user_id=current_user.id,
            service_id=request.service_id,
            title="新对话"
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
    
    return ApiResponse(
        code=200,
        message="success",
        data={
            "id": conversation.id,
            "conversation_id": conversation.conversation_id,
            "service_id": conversation.service_id,
            "title": conversation.title,
            "created_at": conversation.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": conversation.updated_at.strftime("%Y-%m-%d %H:%M:%S")
        }
    )


@app.delete("/api/conversations/{conversation_id}", response_model=ApiResponse)
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除会话"""
    conversation = db.query(Conversation).filter(
        Conversation.conversation_id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )
    
    db.delete(conversation)
    db.commit()
    
    return ApiResponse(code=200, message="删除成功")


# ---------------------------------------------------------------------------
# 消息接口
# ---------------------------------------------------------------------------

@app.post("/api/messages", response_model=ApiResponse)
async def send_message(
    request: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """发送消息（自动触发法律分析）"""
    # 查找或创建会话
    conversation = db.query(Conversation).filter(
        Conversation.conversation_id == request.conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        # 同时在 sessions 表中创建记录（满足 messages 表的外键约束）
        db.execute(text("""
            INSERT INTO sessions (id, user_id, title, service_type) 
            VALUES (:conv_id, :user_id, '新对话', 'qa')
            ON DUPLICATE KEY UPDATE title='新对话'
        """), {"conv_id": request.conversation_id, "user_id": current_user.id})
        
        conversation = Conversation(
            conversation_id=request.conversation_id,
            user_id=current_user.id,
            service_id="qa",
            title="新对话"
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
    
    # 保存用户消息
    user_message = Message(
        session_id=request.conversation_id,  # 使用前端传来的conversation_id作为session_id
        role="user",
        content=request.content
    )
    db.add(user_message)
    
    # 更新会话标题（取第一条消息前20字）
    if conversation.title == "新对话" and request.role == "user":
        conversation.title = request.content[:20] + ("..." if len(request.content) > 20 else "")
    
    db.commit()
    db.refresh(conversation)
    
    # 调用法律分析
    try:
        initial_state: GlobalCaseState = {
            "user_input": request.content,
            "uploaded_files": [],
            "execution_results": [],
            "review_issues": [],
        }
        
        result_state = await asyncio.wait_for(
            asyncio.to_thread(main_graph.invoke, initial_state),
            timeout=_WORKFLOW_TIMEOUT,
        )
        
        # 生成回复内容
        report_content = result_state.get("report_content", "")
        pending_question = result_state.get("pending_question", "")
        info_complete = result_state.get("info_complete", True)
        
        if pending_question and not info_complete:
            assistant_content = pending_question
            status_type = "need_info"
        else:
            assistant_content = report_content or "分析已完成"
            status_type = "completed"
        
        # 保存助手回复
        assistant_message = Message(
            session_id=request.conversation_id,
            role="assistant",
            content=assistant_content
        )
        db.add(assistant_message)
        db.commit()
        
        return ApiResponse(
            code=200,
            message="success",
            data={
                "answer": assistant_content,
                "conversation_id": request.conversation_id,
                "status": status_type,
                "title": conversation.title
            }
        )
        
    except asyncio.TimeoutError:
        return ApiResponse(
            code=500,
            message="分析超时",
            data={"answer": "抱歉，分析时间过长，请稍后重试。", "conversation_id": request.conversation_id}
        )
    except Exception as e:
        logger.error(f"分析异常: {e}", exc_info=True)
        return ApiResponse(
            code=500,
            message="分析失败",
            data={"answer": f"分析失败: {str(e)}", "conversation_id": request.conversation_id}
        )


# ---------------------------------------------------------------------------
# 文件上传接口
# ---------------------------------------------------------------------------

@app.post("/api/legal/upload", response_model=UploadResponse)
async def upload_files(files: list[UploadFile] = File(...)):
    """上传文件到服务器"""
    if not files:
        return UploadResponse(success=False, error="未提供文件")

    uploaded_paths: list[str] = []
    for f in files:
        ext = Path(f.filename or "").suffix.lower()
        supported = {".pdf", ".docx", ".doc", ".txt", ".md"}
        if ext not in supported:
            logger.warning(f"[upload] 跳过不支持的文件格式: {f.filename} ({ext})")
            continue

        unique_name = f"{uuid.uuid4().hex[:8]}_{f.filename}"
        save_path = _UPLOAD_DIR / unique_name

        try:
            with open(save_path, "wb") as out:
                shutil.copyfileobj(f.file, out)
            rel_path = f"uploads/{unique_name}"
            uploaded_paths.append(rel_path)
            logger.info(f"[upload] 文件保存成功: {rel_path}")
        except Exception as e:
            logger.error(f"[upload] 文件保存失败: {f.filename} - {e}")

    if not uploaded_paths:
        return UploadResponse(success=False, error="所有文件上传失败或格式不支持")

    return UploadResponse(success=True, file_paths=uploaded_paths)


# ---------------------------------------------------------------------------
# 分析接口
# ---------------------------------------------------------------------------

@app.get("/api/legal/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "service": "fcs"}


@app.post("/api/legal/analyze", response_model=AnalyzeResponse)
async def analyze_legal(request: AnalyzeRequest):
    """提交法律问题，触发主控工作流执行"""
    session_id = request.session_id or str(uuid.uuid4())
    is_resume = bool(request.session_id and request.user_response)

    steps: list[dict[str, Any]] = []

    try:
        if is_resume:
            logger.info(f"[session:{session_id}] 收到用户回复: {request.user_response[:100]}...")

            prev_session = _session_store.get(session_id, {})
            prev_question = prev_session.get("pending_question", "")
            prev_history = prev_session.get("conversation_history", [])

            conversation_history = list(prev_history)
            if prev_question:
                conversation_history.append({"role": "agent", "content": prev_question})
            conversation_history.append({"role": "user", "content": request.user_response})

            original_input = prev_session.get("original_input", "")
            combined_input = f"{original_input}。{request.user_response}"

            initial_state: GlobalCaseState = {
                "user_input": combined_input,
                "uploaded_files": prev_session.get("uploaded_files", []),
                "conversation_history": conversation_history,
                "info_complete": True,
                "execution_results": [],
                "review_issues": [],
            }

            logger.info(f"[session:{session_id}] 续传重新跑图, 合并输入: {combined_input[:100]}...")

            result_state = await asyncio.wait_for(
                asyncio.to_thread(main_graph.invoke, initial_state),
                timeout=_WORKFLOW_TIMEOUT,
            )

        else:
            if not request.user_input:
                return AnalyzeResponse(success=False, status="error", session_id=session_id, steps=steps)

            logger.info(f"[session:{session_id}] 收到分析请求: {request.user_input[:100]}...")

            initial_state: GlobalCaseState = {
                "user_input": request.user_input,
                "uploaded_files": request.uploaded_files,
                "execution_results": [],
                "review_issues": [],
            }

            result_state = await asyncio.wait_for(
                asyncio.to_thread(main_graph.invoke, initial_state),
                timeout=_WORKFLOW_TIMEOUT,
            )

        pending_question = result_state.get("pending_question", "")
        missing_info = result_state.get("missing_info", [])
        info_complete = result_state.get("info_complete", True)

        if pending_question and not info_complete:
            _session_store[session_id] = {
                "pending_question": pending_question,
                "missing_info": missing_info,
                "conversation_history": result_state.get("conversation_history", []),
                "original_input": result_state.get("user_input", ""),
                "uploaded_files": result_state.get("uploaded_files", []),
            }
            logger.info(f"[session:{session_id}] 需要追问: {pending_question[:100]}...")

            return AnalyzeResponse(
                success=True,
                status="need_info",
                session_id=session_id,
                pending_question=pending_question,
                missing_info=missing_info,
                steps=steps,
            )

        return AnalyzeResponse(
            success=True,
            status="completed",
            session_id=session_id,
            intent=result_state.get("extracted_intent"),
            execution_results=result_state.get("execution_results", []),
            report_content=result_state.get("report_content"),
            review_passed=result_state.get("review_passed"),
            review_issues=result_state.get("review_issues", []),
            user_emotion=result_state.get("user_emotion"),
            steps=steps,
        )

    except asyncio.TimeoutError:
        logger.error(f"[session:{session_id}] 工作流执行超时 ({_WORKFLOW_TIMEOUT}s)")
        return AnalyzeResponse(success=False, status="error", session_id=session_id, steps=steps)

    except Exception as e:
        logger.error(f"[session:{session_id}] 工作流执行异常: {type(e).__name__}: {e}", exc_info=True)
        return AnalyzeResponse(success=False, status="error", session_id=session_id, steps=steps)


# ---------------------------------------------------------------------------
# 启动
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="127.0.0.1",
        port=5000,
        reload=True,
        log_level="info",
    )
