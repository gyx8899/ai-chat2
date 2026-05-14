# AI Chat — 全栈 AI 对话应用

基于 React + FastAPI 的全栈应用，演示 AI 聊天产品的核心能力架构。

## 核心功能

- **SSE 流式输出** — 实时逐字渲染 AI 回答
- **模拟 RAG 检索** — 知识库存静态文件，关键词匹配召回上下文，拼接到提示词引导大模型生成，无需向量库即可跑通「检索-增强生成」全流程
- **多会话历史管理** — 会话持久化，支持按角色类型隔离
- **多模型切换** — 一行配置切换 OpenAI / Ollama / 通义千问 / Mock

## 技术栈

| 层 | 技术 |
|----|------|
| 前端 | Next.js 15（App Router）+ TypeScript + Tailwind CSS + Zustand |
| 后端 | FastAPI（async）+ SQLAlchemy 2（async）+ PostgreSQL / SQLite |
| LLM | OpenAI / Ollama / Mock |
| 协议 | REST + SSE 流式响应 |
| 迁移 | Alembic |

## 快速开始

### 1. 启动后端

```bash
cd backend

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -e ".[dev]"

# 初始化数据库
alembic upgrade head

# 启动（端口 8080）
uvicorn app.main:app --reload --port 8080
```

### 2. 启动前端

```bash
cd frontend

npm install
npm run dev
# 前端运行于 http://localhost:3000
```

### 3. 一体启动（前后端同时运行）

```bash
npm run dev:full
```

## 项目结构

```
ai-chat/
├── backend/                 # FastAPI 后端
│   ├── app/
│   │   ├── main.py          # 入口
│   │   ├── core/           # 配置、常量、异常
│   │   ├── db/             # 数据层（models/schemas）
│   │   ├── domain/         # 领域层（session/llm）
│   │   └── routers/        # API 路由
│   ├── config/
│   │   └── prompts.json    # 提示词配置文件
│   ├── migrations/         # Alembic 迁移脚本
│   └── tests/               # pytest 测试
│
├── frontend/                # Next.js 前端
│   ├── src/
│   │   ├── app/            # App Router 页面
│   │   ├── components/     # UI 组件（ChatArea/Sidebar/MessageList...）
│   │   ├── contexts/       # React Context
│   │   ├── hooks/          # 自定义 Hooks
│   │   ├── store/          # Zustand Store
│   │   └── server/         # 服务端专用模块
│   └── ...
│
└── README.md                # 本文件
```

## 核心功能

### 多提示词切换

提示词定义于 `config/prompts.json`，通过 URL 参数 `?type=` 切换页面角色类型，对应不同 system prompt、welcome 语、examples 示例：

```
?type=default     → 默认助手
?type=frontendAI  → 前端 AI 助手
?type=backendAI   → 后端 AI 助手
?type=writing     → 写作助手
```

每个提示词包含 `content`（system prompt）、`variables`（模板变量）、`preferred_model`（偏好模型）、`is_enabled`（开关）等字段。切换时打开新标签页，隔离会话与上下文。

### 流式对话（SSE）

`POST /api/v1/chat/stream` 返回 Server-Sent Events，按 token 逐帧推送 `{"content": "字"}`。前端使用 `ReadableStream` 消费 SSE 事件，50ms 节流 flush 到 UI 实现打字机效果。流式请求通过 `AbortController` 管理，组件卸载或会话切换时立即中止。

### 会话管理

- `GET /api/v1/sessions/?prompt_type=xxx` 按提示词类型加载会话列表
- 创建会话后自动以第一条用户消息内容命名（截取前 50 字符）
- 消息持久化：用户消息立即落库，助手消息在 SSE 流结束后一次性落库，异常中断时标记 `[已中断]`
- 后端不可用时前端降级为本地会话（内存），网络恢复后可继续操作

### LLM Provider

| Provider | 配置 |
|----------|------|
| Mock | 默认，无需配置，返回固定回复用于开发调试 |
| OpenAI | `LLM_PROVIDER=openai`，需配置 `LLM_API_KEY` |
| Ollama | `LLM_PROVIDER=ollama`，需配置 `LLM_OLLAMA_BASE_URL` |

热重载调用 `POST /api/v1/config/prompts/reload?secret=<RELOAD_SECRET>`，服务端重新解析 JSON → 替换 `PromptService._cache`，同时触发 `revalidateTag('prompts')` 清除 Next.js 服务端缓存，无需重启。

## 环境变量

### 后端

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DATABASE_URL` | 数据库连接 | `sqlite+aiosqlite:///./data/chat.db` |
| `LLM_PROVIDER` | LLM Provider | `mock` |
| `LLM_API_KEY` | OpenAI API Key | — |
| `LLM_MODEL` | 模型名称 | `gpt-4o-mini` |
| `LLM_OLLAMA_BASE_URL` | Ollama 地址 | `http://localhost:11434` |
| `LLM_OLLAMA_MODEL` | Ollama 模型 | `llama3.2` |
| `SERVER_PORT` | 服务端口 | `8080` |

### 前端（.env.local）

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `NEXT_PUBLIC_API_URL` | 后端 API 地址 | `http://localhost:8080` |
| `REVALIDATE_SECRET` | 热更新鉴权密钥 | `revalidate-secret-change-me` |

## 测试

pytest + pytest-asyncio，覆盖 routers、services、providers 全部路径。助手消息持久化采用真实数据库（不 mock），确保 SSE 流中断时 `finally` 块正确执行。

```bash
cd backend
pytest tests/ -v
pytest tests/ --cov=app --cov-report=term-missing
```

## 数据库迁移

Alembic 管理 SQLAlchemy 模型变更，支持 SQLite（开发默认）和 PostgreSQL（生产）。`down_revision` 必须指向实际 revision ID，不可使用逻辑名。

```bash
cd backend

# 升级到最新
alembic upgrade head

# 回滚一个版本
alembic downgrade -1

# 生成新迁移
alembic revision --autogenerate -m "描述"
```

## API 概览

### 会话

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/v1/sessions/` | 列出用户会话，支持 `?prompt_type=` 按提示词类型过滤，返回会话 ID / 标题 / 创建时间 |
| `POST` | `/api/v1/sessions/` | 创建会话（返回后端生成的 UUID / title / prompt_type） |
| `PATCH` | `/api/v1/sessions/{id}` | 更新会话标题（本地会话跳过 API） |
| `DELETE` | `/api/v1/sessions/{id}` | 删除会话及其全部消息 |
| `GET` | `/api/v1/sessions/{id}/messages` | 获取会话消息列表，含 role / content / created_at / metadata |

### 聊天

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/v1/chat/` | 同步对话，等待 LLM 完整响应后返回 |
| `POST` | `/api/v1/chat/stream` | SSE 流式对话，返回 `data: {"content": "字"}\n\n` 逐 token 帧，末尾 `data: [DONE]` |

### 提示词

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/v1/config/prompts/` | 完整提示词列表（`examples` 含 question + answer） |
| `GET` | `/api/v1/config/prompts/list` | 前端专用列表（`examples` 仅 `string[]`） |
| `GET` | `/api/v1/config/prompts/{type_id}` | 获取单条提示词（含渲染后的 system prompt `content`） |
| `POST` | `/api/v1/config/prompts/reload` | 热重载 JSON 配置，重新初始化 PromptService 单例 |

### 系统

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/health` | 健康检查，返回 `{"status": "ok"}` |
| `GET` | `/metrics` | Prometheus 指标（请求延迟 / 错误率 / 在线会话数） |

详细 API 文档参见 [backend/README.md](backend/README.md) 和 [frontend/README.md](frontend/README.md)。

## 许可证

MIT License