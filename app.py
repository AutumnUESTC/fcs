"""法律多智能体系统 - FastAPI 服务入口

提供 HTTP 接口触发主控工作流执行，支持多轮对话和文件上传。

接口：
  POST /api/legal/analyze   — 提交法律问题（首次请求或用户回复）
  POST /api/legal/upload    — 上传文件，返回服务器路径供 analyze 使用
  GET  /api/legal/health    — 健康检查

多轮对话流程：
  1. 客户端发送首次请求（user_input）
  2. 如果系统需要更多信息，返回 status="need_info" + pending_question
  3. 客户端发送回复（session_id + user_response）
  4. 重复 2-3 直到信息完整，系统返回 status="completed" + 报告

文件上传流程：
  1. 客户端先调用 /api/legal/upload 上传文件，获得 file_paths
  2. 将 file_paths 放入 /api/legal/analyze 的 uploaded_files 字段
  3. 系统自动读取文件内容并纳入分析

==========================================================================
前后端对接说明
==========================================================================

【后端接口】

1. POST /api/legal/upload
   - Content-Type: multipart/form-data
   - 参数: files (可多个文件)
   - 返回: {"file_paths": ["uploads/xxx.pdf", ...]}
   - 文件保存到项目根目录的 uploads/ 文件夹

2. POST /api/legal/analyze
   - Content-Type: application/json
   - 参数:
     {
       "user_input": "用户的法律问题",        // 首次请求必填
       "uploaded_files": ["uploads/xxx.pdf"],  // 上传接口返回的路径
       "session_id": "",                       // 续传时填上次返回的 session_id
       "user_response": ""                     // 续传时填用户对追问的回复
     }
   - 返回:
     - status="need_info":  需要追问，前端展示 pending_question 并让用户回复
     - status="completed":  完成，前端展示 report_content
     - status="error":      出错，前端展示 steps 中的调试信息

【前端示例 (Vue 3 + TypeScript)】

// 1. 上传文件
async function uploadFiles(files: File[]): Promise<string[]> {
  const formData = new FormData()
  files.forEach(f => formData.append('files', f))
  const res = await fetch('http://localhost:8000/api/legal/upload', {
    method: 'POST',
    body: formData,
  })
  const data = await res.json()
  return data.file_paths  // ["uploads/xxx.pdf", ...]
}

// 2. 提交分析（首次）
async function submitAnalyze(userInput: string, filePaths: string[] = []) {
  const res = await fetch('http://localhost:8000/api/legal/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_input: userInput,
      uploaded_files: filePaths,
      session_id: '',
      user_response: '',
    }),
  })
  return await res.json()
  // 如果返回 status="need_info"，保存 session_id，展示追问，等待用户回复
}

// 3. 回复追问（续传）
async function replyQuestion(sessionId: string, userResponse: string) {
  const res = await fetch('http://localhost:8000/api/legal/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_input: '',
      uploaded_files: [],
      session_id: sessionId,
      user_response: userResponse,
    }),
  })
  return await res.json()
}

【前端示例 (原生 JavaScript / fetch)】

// 上传文件
const formData = new FormData()
formData.append('files', fileInput.files[0])
const uploadRes = await fetch('/api/legal/upload', { method: 'POST', body: formData })
const { file_paths } = await uploadRes.json()

// 提交分析
const analyzeRes = await fetch('/api/legal/analyze', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    user_input: '商业秘密被泄露，能申请禁令吗',
    uploaded_files: file_paths,
  }),
})
const result = await analyzeRes.json()
if (result.status === 'need_info') {
  // 展示 result.pending_question，让用户回复
  // 保存 result.session_id 用于续传
}
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
from typing import Any

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from agents.main_graph import main_graph
from agents.states import GlobalCaseState

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
        logging.StreamHandler(),  # 控制台输出 (INFO+)
        logging.FileHandler(_LOG_DIR / f"fcs_{_log_timestamp}.log", encoding="utf-8"),  # 文件输出 (INFO+)
    ],
)

# 额外: 文件中记录 DEBUG 级别日志（包含小理 API 完整响应等）
_file_debug_handler = logging.FileHandler(_LOG_DIR / f"fcs_debug_{_log_timestamp}.log", encoding="utf-8")
_file_debug_handler.setLevel(logging.DEBUG)
_file_debug_handler.setFormatter(logging.Formatter("%(asctime)s [%(name)s] %(message)s"))
logging.getLogger("agents").addHandler(_file_debug_handler)
logging.getLogger("agents").setLevel(logging.DEBUG)
logger = logging.getLogger("fcs.server")

# 工作流超时时间（秒）— 防止 LLM 响应慢导致请求卡死
_WORKFLOW_TIMEOUT = int(os.getenv("FCS_WORKFLOW_TIMEOUT", "600"))

# 会话存储：保存每轮对话的 pending_question 等信息，用于多轮对话续传
# key: session_id, value: {"pending_question": str, "missing_info": list, "conversation_history": list}
_session_store: dict[str, dict[str, Any]] = {}


# ---------------------------------------------------------------------------
# 请求 / 响应模型
# ---------------------------------------------------------------------------


class AnalyzeRequest(BaseModel):
    """法律分析请求"""
    # 首次请求必填
    user_input: str = Field(
        default="",
        description="用户的法律问题或诉求描述（首次请求必填，回复轮次可为空）",
    )
    uploaded_files: list[str] = Field(
        default_factory=list,
        description=(
            "用户上传的文件路径列表（由 /api/legal/upload 接口返回）。"
            "例如: ['uploads/xxx.pdf', 'uploads/yyy.docx']"
        ),
    )
    # 多轮对话续传
    session_id: str = Field(
        default="",
        description="会话ID（首次请求可不填，自动生成；续传时必填）",
    )
    user_response: str = Field(
        default="",
        description="用户对追问的回复（仅续传轮次使用）",
    )


class AnalyzeResponse(BaseModel):
    """法律分析响应"""
    success: bool
    status: str = "completed"  # "completed" | "need_info" | "error"
    session_id: str = ""

    # need_info 时
    pending_question: str = ""
    missing_info: list[str] = []

    # completed 时
    intent: dict[str, Any] | None = None
    execution_results: list[dict[str, Any]] = []
    report_content: str | None = None
    review_passed: bool | None = None
    review_issues: list[str] = []

    # 情绪分析结果
    user_emotion: dict[str, Any] | None = None

    # 调试信息
    steps: list[dict[str, Any]] = []


class UploadResponse(BaseModel):
    """文件上传响应"""
    success: bool
    file_paths: list[str] = Field(
        default_factory=list,
        description="上传成功后的文件路径列表，供 /api/legal/analyze 的 uploaded_files 字段使用",
    )
    error: str = ""


# ---------------------------------------------------------------------------
# 应用生命周期
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
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
# 文件上传接口
# ---------------------------------------------------------------------------


@app.post("/api/legal/upload", response_model=UploadResponse)
async def upload_files(files: list[UploadFile] = File(...)):
    """上传文件到服务器，返回文件路径供后续分析使用。

    支持格式：PDF、DOCX、DOC、TXT、MD

    使用方式：
      1. 前端通过 multipart/form-data 上传一个或多个文件
      2. 接口返回 file_paths 列表
      3. 将 file_paths 传入 /api/legal/analyze 的 uploaded_files 字段

    示例 (curl):
      curl -X POST http://localhost:8000/api/legal/upload \\
        -F "files=@/path/to/contract.pdf" \\
        -F "files=@/path/to/evidence.docx"

    示例 (前端 JavaScript):
      const formData = new FormData()
      formData.append('files', fileInput.files[0])
      const res = await fetch('/api/legal/upload', { method: 'POST', body: formData })
      const { file_paths } = await res.json()
    """
    if not files:
        return UploadResponse(success=False, error="未提供文件")

    uploaded_paths: list[str] = []
    for f in files:
        # 检查文件扩展名
        ext = Path(f.filename or "").suffix.lower()
        supported = {".pdf", ".docx", ".doc", ".txt", ".md"}
        if ext not in supported:
            logger.warning(f"[upload] 跳过不支持的文件格式: {f.filename} ({ext})")
            continue

        # 生成唯一文件名避免冲突
        unique_name = f"{uuid.uuid4().hex[:8]}_{f.filename}"
        save_path = _UPLOAD_DIR / unique_name

        try:
            with open(save_path, "wb") as out:
                shutil.copyfileobj(f.file, out)
            # 返回相对于项目根目录的路径
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
    """提交法律问题，触发主控工作流执行

    多轮对话模式（不使用 interrupt，由 API 层控制）：
      - 首次请求：提供 user_input，系统自动生成 session_id
      - 追问回复：提供 session_id + user_response
      - 系统在需要更多信息时返回 status="need_info"
      - 信息完整后返回 status="completed" + 分析报告
    """
    # 确定 session_id
    session_id = request.session_id or str(uuid.uuid4())

    # 判断是首次请求还是续传
    is_resume = bool(request.session_id and request.user_response)

    steps: list[dict[str, Any]] = []

    try:
        if is_resume:
            # 续传：用户回复追问
            logger.info(f"[session:{session_id}] 收到用户回复: {request.user_response[:100]}...")

            # 从会话存储获取之前的追问信息
            prev_session = _session_store.get(session_id, {})
            prev_question = prev_session.get("pending_question", "")
            prev_history = prev_session.get("conversation_history", [])

            # 拼接对话历史：之前的追问 + 用户的回复
            conversation_history = list(prev_history)  # 复制
            if prev_question:
                conversation_history.append({"role": "agent", "content": prev_question})
            conversation_history.append({"role": "user", "content": request.user_response})

            # 构建新的初始状态，把用户原始输入 + 回复合并
            original_input = prev_session.get("original_input", "")
            combined_input = f"{original_input}。{request.user_response}"

            initial_state: GlobalCaseState = {
                "user_input": combined_input,
                "uploaded_files": prev_session.get("uploaded_files", []),
                "conversation_history": conversation_history,
                "info_complete": True,  # 用户已回复追问，标记信息完整
                "execution_results": [],
                "review_issues": [],
            }

            logger.info(f"[session:{session_id}] 续传重新跑图, 合并输入: {combined_input[:100]}...")

            # 重新跑图（同首次请求一样用 invoke）
            result_state = await asyncio.wait_for(
                asyncio.to_thread(main_graph.invoke, initial_state),
                timeout=_WORKFLOW_TIMEOUT,
            )

        else:
            # 首次请求
            if not request.user_input:
                return AnalyzeResponse(
                    success=False,
                    status="error",
                    session_id=session_id,
                    steps=steps,
                )

            logger.info(f"[session:{session_id}] 收到分析请求: {request.user_input[:100]}...")

            initial_state: GlobalCaseState = {
                "user_input": request.user_input,
                "uploaded_files": request.uploaded_files,
                "execution_results": [],
                "review_issues": [],
            }

            # 启动工作流
            result_state = await asyncio.wait_for(
                asyncio.to_thread(main_graph.invoke, initial_state),
                timeout=_WORKFLOW_TIMEOUT,
            )

        # 检查结果：是否需要追问
        pending_question = result_state.get("pending_question", "")
        missing_info = result_state.get("missing_info", [])
        info_complete = result_state.get("info_complete", True)

        if pending_question and not info_complete:
            # 需要追问，保存会话信息用于续传
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

        # 工作流完成
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
        return AnalyzeResponse(
            success=False,
            status="error",
            session_id=session_id,
            steps=steps,
        )

    except Exception as e:
        logger.error(f"[session:{session_id}] 工作流执行异常: {type(e).__name__}: {e}", exc_info=True)
        return AnalyzeResponse(
            success=False,
            status="error",
            session_id=session_id,
            steps=steps,
        )


# ---------------------------------------------------------------------------
# 启动
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
