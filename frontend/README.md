# AI Chat — Frontend

Next.js 15 前端，基于 App Router、React Server Components 和 Tailwind CSS。

## 技术栈

| 分类 | 技术 |
|------|------|
| 框架 | Next.js 15.3（App Router + RSC） |
| 语言 | TypeScript 5 |
| 样式 | Tailwind CSS 4 + Radix UI |
| 状态管理 | Zustand 5 |
| 国际化 | 自定义 useTranslation Hook |
| Markdown | react-markdown + remark-gfm |
| Lint | ESLint 9 + Prettier |
| 测试 | Vitest + Testing Library |

## 快速开始

### 前置依赖

- Node.js >= 20
- 后端服务运行于 `http://localhost:8080`

### 安装与启动

```bash
cd frontend

# 安装依赖
npm install

# 开发模式（仅前端，需后端单独启动）
npm run dev

# 前后端一体开发（启动后端 + 前端）
npm run dev:full
```

### 环境变量

```bash
cp .env.example .env.local
# 编辑 .env.local，配置以下变量
```

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `NEXT_PUBLIC_API_URL` | 后端 API 地址 | `http://localhost:8080` |
| `BACKEND_INTERNAL_URL` | 服务端调用后端的内部地址（SSR 直出时使用） | `http://localhost:8080` |
| `REVALIDATE_SECRET` | 热更新 revalidate 鉴权密钥 | `revalidate-secret-change-me` |

## 目录结构

```
src/
├── app/                    # Next.js App Router 页面
│   ├── page.tsx            # 首页 RSC（SSR 入口）
│   ├── ChatPageClient.tsx  # Client Component 外壳
│   ├── api/                # 前端 API 路由（如 revalidate-prompts）
│   └── sessions/           # 会话管理页面
├── components/             # UI 组件
│   ├── ChatArea/           # 聊天主区域
│   ├── MessageList/        # 消息列表
│   ├── InputArea/          # 输入框
│   ├── Sidebar/            # 侧边栏（会话列表）
│   ├── PromptSelector/     # 提示词选择器
│   ├── ModelSelector/      # 模型选择器
│   └── ui/                 # Radix UI 基础组件
├── contexts/               # React Context
│   └── PromptsContext.tsx  # 提示词上下文
├── hooks/                  # 自定义 Hooks
│   ├── useChat.ts          # 聊天核心（发送/流式/SSE）
│   ├── usePromptType.ts    # URL type 参数同步
│   ├── useSyncPreferredModel.ts  # 模型偏好同步
│   └── ...
├── store/                  # Zustand Store
│   ├── sessionStore.ts     # 会话 + 消息状态
│   ├── chatStore.ts        # 聊天状态（loading/ragHint）
│   ├── modelStore.ts       # 模型列表状态
│   └── uiStore.ts          # UI 状态（侧栏开关等）
├── server/                 # 服务端专用模块
│   └── prompts.ts          # RSC 调用后端提示词 API
└── lib/                    # 工具函数
    ├── sseClient.ts        # SSE 客户端
    └── ...
```

## 核心设计

### 提示词系统

提示词配置从后端 `config/prompts.json` 加载，通过 URL 参数 `?type=frontendAI` 切换页面提示词类型。

```
?type=default    → 默认助手
?type=frontendAI → 前端 AI 助手
?type=backendAI  → 后端 AI 助手
?type=writing    → 写作助手
```

**SSR 直出流程**：
1. `page.tsx`（RSC）调用 `getPrompts()` 从后端获取提示词列表
2. 服务端直出不含 `content` 的菜单数据（`welcome/examples/preferred_model`）
3. `ChatPageClient` 包裹 `PromptsProvider`，通过 Context 下发配置
4. 切换提示词时打开新浏览器标签页，原页面不变

**降级机制**：后端不可用时，前端使用本地 `lib/promptDefaults.ts` 内置常量作为降级提示词，`isDegraded` 标志位决定是否显示降级提示。

### 会话与消息

- **会话列表**：`Sidebar` 根据 URL `type` 参数调用 `GET /api/v1/sessions/?prompt_type=xxx` 加载对应会话
- **消息加载**：`selectSession(sessionId)` 调用 `GET /api/v1/sessions/{id}/messages` 获取历史消息
- **消息发送**：通过 `useChat` Hook 使用 SSE 流式发送，`/api/v1/chat/stream`

### 状态流

```
page.tsx (RSC)
  └── ChatPageClient (Client)
        └── PromptsProvider (Context)
              ├── Sidebar (会话列表)
              │     └── loadSessions(type) → selectSession(id)
              └── ChatArea
                    ├── MessageList (activeMessages)
                    ├── EmptyState (welcome + examples)
                    └── InputArea → useChat.send() → SSE
```

## 构建与部署

```bash
# 类型检查
npm run type-check

# Lint
npm run lint

# 构建生产版本
npm run build

# 启动生产服务
npm start
```

## 开发规范

- 所有前端路由页面均为 RSC，数据获取在服务端完成
- 敏感数据（提示词 `content`）仅在后端存储，通过 Context 下发公开字段
- 会话状态由 Zustand 管理，`activeMessages` 为当前会话消息
- 使用 `import type` 导入服务端模块，避免 Client Component 违规引用