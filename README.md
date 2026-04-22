# 法脉智联 (FCS) - 法律多智能体系统

基于 LangGraph 的法律多智能体协作系统，支持多轮对话、情感分析、合同审查、法规查询等功能。前端采用 Vue 3 + Vite 构建，提供流畅的对话交互体验。

## 系统架构

```
START → orchestrator ⇄ wait_for_user → executor → reporter → reviewer → END
              ↑              │                ↑           ↑          │
              └──────────────┘                └───────────┴──────────┘
             (need_info)                      (rollback 条件边)
```

### 核心流程

1. **orchestrator（调度节点）** — 分析用户情绪、分类法律意图、查询相关法规、判断信息完整性
2. **wait_for_user（等待用户）** — 当信息不完整时，通过 interrupt 暂停工作流，等待用户补充信息
3. **executor（执行节点）** — 根据意图分析结果执行法律查询、合同审查等任务
4. **reporter（报告节点）** — 生成法律分析报告，并根据用户情绪润色报告语气
5. **reviewer（审核节点）** — 校验报告中的法条引用和逻辑一致性

### 回滚机制

任何节点发现严重问题时，可以通过 `rollback_signal` 回退到之前的节点重试：
- reviewer → reporter / executor / orchestrator
- reporter → executor / orchestrator
- executor → orchestrator

## 项目结构

```
fcs-1/
├── app.py                      # FastAPI 服务入口（HTTP API）
├── auth.py                     # 用户认证模块（JWT）
├── database.py                 # 数据库模型与初始化（SQLAlchemy + SQLite）
├── init_db.py                  # 数据库初始化脚本
├── requirements.txt            # Python 依赖
├── start.bat                   # Windows 一键启动脚本
├── start.sh                    # Linux/Mac 一键启动脚本
├── agents/
│   ├── __init__.py             # 包导出
│   ├── states.py               # 全局状态定义（GlobalCaseState, NodeSubState, PlannerDecision）
│   ├── main_graph.py           # 主控工作流图（LangGraph StateGraph）
│   ├── node_subgraph.py        # 节点子图构建器（planner 循环）
│   ├── planner.py              # 通用 Planner 控制器（Mock / LLM 模式）
│   ├── orchestrator_agent.py   # 意图分类与任务拆解工具
│   ├── executor_agent.py       # 任务执行相关（已集成到 tools.py）
│   ├── report_agent.py         # 报告生成智能体
│   ├── reviewer_agents.py      # 报告审核智能体
│   ├── verifier_agent.py       # 事实核查智能体
│   ├── emotion_agent.py        # 情感分析智能体
│   ├── polish_agent.py         # 文本润色智能体
│   ├── legal_query_agent.py    # 法律知识库查询智能体
│   ├── file_reader.py          # 文件读取工具（PDF/DOCX/TXT）
│   ├── drafting_subgraph.py    # 红蓝对抗审查子图
│   ├── tools.py                # @tool 注册中心（所有工具的统一入口）
│   ├── llm_factory.py          # LLM 工厂（当前 Mock 模式）
│   ├── api.py                  # Python API 入口（支持多轮对话）
│   └── 工作流示例.md            # 工作流说明文档
└── fronted_v2/                 # 前端 Vue 3 项目
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── api/chat.js         # 前端 API 调用层
        ├── layouts/UserLayout.vue  # 主布局（侧边栏 + 会话列表）
        ├── views/
        │   ├── user/ChatPage.vue   # 聊天页面（消息收发 + 流式输出）
        │   └── pages/AboutPage.vue # 关于页面
        └── ...
```

## 快速开始

### 环境要求

- **Python** 3.10+（推荐使用 Conda 管理）
- **Node.js** 18+
- **Conda**（可选，推荐）

### 一键启动

#### Windows

双击 `start.bat` 或在项目根目录运行：

```cmd
start.bat
```

#### Linux / Mac

```bash
chmod +x start.sh
./start.sh
```

启动脚本会自动完成以下操作：
1. 检查 Conda 环境（如已安装，让你选择使用哪个环境）
2. 检查 Python 和 Node.js
3. 安装后端 Python 依赖
4. 安装前端 Node.js 依赖（已有 node_modules 则跳过）
5. 初始化数据库（含兼容迁移）
6. 启动后端服务（`http://localhost:5000`）
7. 启动前端服务（`http://localhost:3000`）

### 手动启动

```bash
# 1. 激活 Conda 环境（如使用 Conda）
conda activate your_env_name

# 2. 安装后端依赖
pip install -r requirements.txt

# 3. 初始化数据库
python init_db.py

# 4. 启动后端
python app.py

# 5. 安装前端依赖并启动
cd fronted_v2
npm install
npx vite
```

启动完成后访问 **http://localhost:3000**

## 核心设计

### 1. 分层状态管理

```
GlobalCaseState（主工作流全局状态）
  ├── user_input              # 用户原始输入
  ├── user_emotion            # 情绪分析结果（orchestrator 写入）
  ├── extracted_intent        # 意图解析结果（orchestrator 写入）
  ├── conversation_history    # 多轮对话历史
  ├── pending_question        # 当前追问（need_info 时设置）
  ├── missing_info            # 缺少的信息列表
  ├── info_complete           # 信息是否周全
  ├── execution_results       # 执行结果（executor 写入）
  ├── report_content          # 报告内容（reporter 写入）
  ├── review_passed           # 审核结果（reviewer 写入）
  └── rollback_signal         # 回滚信号

NodeSubState（子图内部状态）
  ├── planner_decision        # Planner 的决策
  ├── planner_thoughts        # 思考历史
  ├── tool_results            # 工具调用结果
  └── ...（从 GlobalCaseState 传入的字段）
```

### 2. 情绪分析 → 报告润色

系统在 orchestrator 节点的第一步执行 `analyze_emotion`，分析用户情绪（焦虑/愤怒/悲伤/困惑/平静），结果存入 `state.user_emotion`。

在 reporter 节点生成报告后，调用 `polish_report` 根据情绪调整报告语气：

| 情绪 | 开场白 | 结束语 | 语气 |
|------|--------|--------|------|
| anxious | 理解您的焦虑...请放心... | 建议尽快采取行动... | reassuring |
| angry | 完全理解您的心情...法律为您提供了... | 您的合法权益受法律保护... | empathetic_firm |
| sad | 非常理解您的处境... | 法律是您最有力的后盾... | gentle_supportive |
| confused | 以下是为您梳理的...按步骤说明 | 如仍有疑问，建议进一步咨询... | clear_structured |
| calm | 以下是法律分析报告 | 以上分析供您参考... | professional |

### 3. 多轮对话（interrupt 机制）

使用 LangGraph 的 `interrupt` + `MemorySaver` 实现工作流暂停/恢复：

```
客户端                             后端
  │                                 │
  │── POST /api/legal/analyze ─────→│  user_input="我的商业秘密被泄露了..."
  │                                 │  → orchestrator 执行
  │                                 │  → info_complete=False
  │                                 │  → interrupt 暂停
  │←─ status="need_info" ──────────│  pending_question="还需要了解..."
  │   + session_id                  │
  │                                 │
  │── POST /api/legal/analyze ─────→│  session_id=xxx, user_response="我们签了保密协议..."
  │                                 │  → Command(resume=user_response)
  │                                 │  → orchestrator 继续分析
  │                                 │  → info_complete=True
  │                                 │  → executor → reporter → reviewer
  │←─ status="completed" ──────────│  report_content=... review_passed=true
  │   + user_emotion                │
```

### 4. 子图内部循环

每个主图节点内部是一个子图，结构相同：

```
planner_node → route_decision ──→ tool_executor ──→ planner_node (继续思考)
                     │
                     ├── action=node_done → 返回主图
                     ├── action=rollback  → 返回主图（带回滚信号）
                     └── action=need_info → 返回主图（带追问信息，仅 orchestrator）
```

各节点的工具集不同：

| 节点 | 可用工具 |
|------|---------|
| orchestrator | `analyze_emotion`, `classify_intent`, `decompose_tasks`, `use_file_reader`, `use_legal_query`, `analyze_info_completeness` |
| executor | `use_legal_query`, `use_contract_review`, `use_verifier` |
| reporter | `use_report_generator`, `polish_report` |
| reviewer | `use_verifier`, `use_legal_query` |

## API 接口

### 认证相关

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/register` | 用户注册 |
| POST | `/api/auth/login` | 用户登录 |

### 法律分析

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/legal/analyze` | 提交法律问题（支持多轮对话） |
| POST | `/api/legal/upload` | 上传文件（PDF/DOCX/TXT） |
| GET  | `/api/legal/health` | 健康检查 |

### 会话管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET  | `/api/conversations` | 获取会话列表 |
| GET  | `/api/conversations/:id` | 获取会话详情（含消息历史） |
| POST | `/api/conversations` | 保存/更新会话 |
| POST | `/api/messages` | 发送消息 |

### 示例

```python
import httpx

# 提交法律问题
response = httpx.post("http://localhost:5000/api/legal/analyze", json={
    "user_input": "我的商业秘密被泄露了，能申请禁令吗？",
}).json())

# 如果需要追问
if response["status"] == "need_info":
    session_id = response["session_id"]

    # 回复追问
    response = httpx.post("http://localhost:5000/api/legal/analyze", json={
        "session_id": session_id,
        "user_response": "我们签了保密协议，前员工拷贝了客户数据...",
    }).json()

# 最终结果
if response["status"] == "completed":
    print(f"报告: {response['report_content']}")
```

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `XIAOLI_APPID` | 小理 AI 法律知识库 AppID | 内置 |
| `XIAOLI_SECRET` | 小理 AI 法律知识库 Secret | 内置 |
| `XIAOLI_BASE_URL` | 小理 AI API 地址 | 内置 |
| `XIAOLI_TIMEOUT` | 小理 AI 请求超时（秒） | 30 |
| `LLM_MODEL` | LLM 模型名称（未来） | gpt-4o-mini |
| `LLM_API_KEY` | LLM API Key（未来） | - |
| `LLM_BASE_URL` | LLM API 地址（未来） | - |

## 技术栈

### 后端
- **LangGraph** — 工作流编排（StateGraph、interrupt、MemorySaver）
- **LangChain** — 工具注册（@tool）、Agent 抽象
- **FastAPI** — HTTP API 服务
- **SQLAlchemy** — ORM（SQLite 数据库）
- **JWT** — 用户认证
- **httpx** — 外部 API 调用（小理法律知识库）
- **Pydantic** — 数据验证

### 前端
- **Vue 3** — 渐进式前端框架
- **Vite** — 构建工具
- **Vue Router** — 路由管理
- **Pinia** — 状态管理

## 待实现

- [ ] 真实 LLM 接入（当前为 Mock 模式，Planner 使用预设策略）
- [ ] 流式 HTTP 响应（SSE）
- [ ] 更多意图类型支持
