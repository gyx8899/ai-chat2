# AI Chat — Backend

FastAPI + async SQLAlchemy 后端，提供 LLM 对话、会话管理、提示词配置等 REST/SSE API。

## 技术栈

| 分类 | 技术 |
|------|------|
| 框架 | FastAPI >= 0.110 |
| 语言 | Python >= 3.10 |
| 数据库 | SQLAlchemy 2（async）+ PostgreSQL / SQLite |
| ORM 迁移 | Alembic |
| LLM 集成 | OpenAI / Ollama / Mock |
| API 协议 | REST + SSE 流式响应 |
| 配置 | Pydantic Settings |
| 日志 | structlog |
| 监控 | Prometheus 指标 |
| 测试 | pytest + pytest-asyncio |

## 快速开始

### 前置依赖

- Python >= 3.10
- Node.js >= 20（前端）
- PostgreSQL 16（可选，默认使用 SQLite）

### 安装与启动

```bash
cd backend

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装依赖
pip install -e ".[dev]"

# 初始化数据库迁移
alembic upgrade head

# 启动开发服务器（端口 8080）
uvicorn app.main:app --reload --port 8080
```

### 环境变量

通过 `.env` 文件配置（参考 `app/core/settings.py` 中的 `BaseSettings` 和 `env_prefix`）：

| 变量前缀 | 说明 | 示例 |
|---------|------|------|
| `DATABASE_` | 数据库连接 | `DATABASE_URL=postgresql+asyncpg://user:pass@host/db` |
| `LLM_` | LLM Provider | `LLM_PROVIDER=openai`，`LLM_MODEL=gpt-4o-mini` |
| `SERVER_` | 服务器 | `SERVER_PORT=8080` |
| `API_` | API 配置 | `API_DEBUG=true` |
| `PROMPT_` | 提示词 | `PROMPT_CONFIG_PATH=config/prompts.json` |

默认使用 SQLite：`sqlite+aiosqlite:///./data/chat.db`（`data/` 目录会自动创建）。

### LLM Provider 配置

```bash
# Mock（默认，无须配置）
LLM_PROVIDER=mock

# OpenAI
LLM_PROVIDER=openai
LLM_API_KEY=sk-...

# Ollama（本地模型）
LLM_PROVIDER=ollama
LLM_OLLAMA_BASE_URL=http://localhost:11434
LLM_OLLAMA_MODEL=llama3.2
```

## 目录结构

```
app/
├── main.py                    # FastAPI 入口，中间件注册，路由挂载
├── core/                      # 核心基础设施
│   ├── constants.py           # 常量定义（消息角色、SSE 事件类型等）
│   ├── exceptions.py          # 统一业务异常
│   ├── llm_config.py         # LLM 配置读取
│   ├── settings.py           # Pydantic Settings 统一配置
│   └── prompts/              # 提示词模块
│       ├── loader.py         # JSON 文件加载 + 校验
│       ├── renderer.py       # {变量} 模板渲染
│       ├── schemas.py        # Pydantic 模型（PromptTemplate/PromptInfo）
│       └── service.py        # PromptService 单例（init/reload/list）
├── db/                        # 数据访问层
│   ├── database.py           # 引擎/会话工厂/get_db 依赖
│   ├── schemas.py            # 请求/响应 Pydantic 模型
│   └── models/               # SQLAlchemy 模型
│       ├── session.py        # Session 模型（含 prompt_type 字段）
│       └── message.py        # Message 模型（含 msg_metadata 字段）
├── domain/                    # 领域层
│   ├── session/
│   │   └── memory_service.py # MemoryService（会话/消息 CRUD）
│   └── llm/                  # LLM 集成
│       ├── llm_service.py    # 统一入口
│       └── providers/        # Provider 实现（mock/openai/ollama）
├── routers/                   # API 路由
│   ├── chat.py              # /api/v1/chat（同步 + SSE 流式）
│   ├── sessions.py          # /api/v1/sessions（CRUD + 消息列表）
│   ├── config.py            # /api/v1/config（LLM 配置）
│   └── prompts.py           # /api/v1/config/prompts（提示词列表/reload）
├── integrations/              # 外部集成（RAG 等）
├── knowledge/                # 知识检索
├── observability/           # 可观测性（日志/指标/中间件）
├── reliability/             # 可靠性（重试/熔断）
├── data/                    # SQLite 数据文件目录
└── migrations/              # Alembic 迁移脚本
    └── versions/
config/
└── prompts.json             # 提示词配置文件（JSON）
```

## API 概览

### 会话管理

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/v1/sessions/` | 列出会话（支持 `?prompt_type=` 过滤） |
| `POST` | `/api/v1/sessions/` | 创建会话 |
| `GET` | `/api/v1/sessions/{id}` | 获取会话详情 |
| `PATCH` | `/api/v1/sessions/{id}` | 更新会话标题 |
| `DELETE` | `/api/v1/sessions/{id}` | 删除会话 |
| `GET` | `/api/v1/sessions/{id}/messages` | 获取消息列表 |

### 聊天

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/v1/chat/` | 同步对话（等待完整响应） |
| `POST` | `/api/v1/chat/stream` | SSE 流式对话 |

SSE 流式协议（`/chat/stream`）：

```
# 请求体
{"query": "问题", "session_id": "uuid", "model": "gpt-4o-mini", "prompt_id": "frontendAI"}

# 响应帧
event: meta   → {"ragHint": "..."}           # RAG 提示
data: {"content": "你"}                        # token 流
data: {"content": "好"}
...
data: [DONE]                                  # 结束
```

### 提示词

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/v1/config/prompts/` | 列出提示词（含分类，`examples` 为 `{question, answer}[]`） |
| `GET` | `/api/v1/config/prompts/list` | 列出提示词（前端专用，`examples` 为 `string[]`，仅 `question`） |
| `GET` | `/api/v1/config/prompts/{type_id}` | 获取单条提示词（含 `content`） |
| `POST` | `/api/v1/config/prompts/reload?secret=xxx` | 热重载提示词配置 |

### 系统

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/health` | 健康检查 |
| `GET` | `/metrics` | Prometheus 指标 |
| `GET` | `/` | 服务信息 |

## 提示词配置

提示词定义在 `config/prompts.json`：

```json
{
  "prompts": [
    {
      "id": "frontend-ai",
      "type": "frontendAI",
      "name": "前端 AI 助手",
      "description": "专注于前端开发的技术助手",
      "category": "development",
      "content": "你是前端技术专家...",
      "variables": [
        {"name": "user_name", "description": "用户名", "default": "用户"}
      ],
      "welcome": "你好！我是前端 AI 助手...",
      "examples": [
        "如何优化首屏加载？",
        "如何实现响应式布局？"
      ],
      "preferred_model": "claude-sonnet-4",
      "is_enabled": true
    }
  ],
  "default_type": "default"
}
```

**热重载**：修改 `prompts.json` 后调用 `POST /api/v1/config/prompts/reload?secret=<reload_secret>`，后端重新加载配置并通知前端清除 Next.js 缓存。

## 数据库迁移

```bash
# 查看当前版本
alembic current

# 查看迁移历史
alembic history

# 升级到最新
alembic upgrade head

# 回滚一个版本
alembic downgrade -1

# 生成新迁移（修改模型后）
alembic revision --autogenerate -m "描述"
```

## 测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行指定文件
pytest tests/test_prompts_router.py -v

# 带覆盖率
pytest tests/ --cov=app --cov-report=term-missing
```

## 架构说明

### DDD 分层

```
routers/    → API 层（接收请求，返回响应）
    ↓
domain/     → 领域层（业务逻辑，MemoryService 等）
    ↓
db/         → 数据层（SQLAlchemy 模型，session 管理）
```

### 消息持久化流程（SSE 流式）

```
1. 保存用户消息 → DB
2. 加载历史消息 → 构建 context
3. 组装 messages（含 system prompt + history + user）
4. 流式调用 LLM → yield content 帧
5. finally: 保存 assistant 消息 → DB（断开时标记 [已中断]）
```

### 提示词解析优先级

```
1. system_prompt（请求体 override）  ← 最高
2. prompt_id（当前会话类型）        ← 次高
3. default_type（prompts.json）     ← 默认