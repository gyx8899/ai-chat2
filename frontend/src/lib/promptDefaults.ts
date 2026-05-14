/**
 * 内置提示词降级默认值。
 *
 * 当后端 /api/v1/config/prompts/list 不可用时（网络错误或超时），
 * 前端使用此列表作为 fallback，保证页面仍可正常渲染。
 *
 * 字段与 backend/app/core/prompts/schemas.py 的 PromptConfigResponse 对齐。
 * 不含 content（安全要求），列表中仅包含 menu 展示所需字段：
 *   id / name / type / category / description / is_enabled
 * 以及 welcome / preferred_model / examples（来自 extra 字段）。
 *
 * 注意：此列表必须与 backend/config/prompts.json 中的 type 字段完全对齐，
 *       用于 isDegraded 判断（逐项比对 id + type）。
 */

/** 每个提示词的最小降级信息 */
export interface PromptDefaultItem {
  id: string
  name: string
  type: string
  category: string
  description: string
  is_enabled: boolean
  /** 欢迎语，用于首页 / 空状态展示 */
  welcome?: string
  /** 用户偏好的模型 ID */
  preferred_model?: string
  /** 示例问题列表 */
  examples?: string[]
}

/**
 * 降级默认值列表。
 * 必须与 backend/config/prompts.json 中的 type 字段完全对齐，
 * 顺序和数量必须一致，用于 isDegraded 正确判断。
 */
export const PROMPT_DEFAULTS: PromptDefaultItem[] = [
  {
    id: 'default',
    name: '默认助手',
    type: 'default',
    category: 'general',
    description: '通用 AI 助手模式，适用于日常问答和各类任务',
    is_enabled: true,
    welcome: '你好，我是小智！有什么我可以帮助你的吗？',
    preferred_model: undefined,
    examples: ['帮我解释一下什么是 REST API'],
  },
  {
    id: 'frontend-ai',
    name: '前端 AI 助手',
    type: 'frontendAI',
    category: 'development',
    description: '专注于前端开发的技术助手，精通 React/Vue/Next.js/TypeScript/CSS',
    is_enabled: true,
    welcome: '你好！我是前端 AI 助手，专注于 React、Vue、Next.js、TypeScript 等前端技术。有什么前端相关的问题可以问我！',
    preferred_model: 'claude-sonnet-4',
    examples: [
      '如何优化 Next.js 首屏加载性能？',
      'React useEffect 的依赖数组为空会怎样？',
    ],
  },
  {
    id: 'backend-ai',
    name: '后端 AI 助手',
    type: 'backendAI',
    category: 'development',
    description: '专注于后端开发的技术助手，精通 Python/FastAPI/Node.js/数据库/微服务',
    is_enabled: true,
    welcome: '你好！我是后端 AI 助手，专注于 Python、Node.js、数据库设计、微服务架构等后端技术。有什么后端相关的问题可以问我！',
    preferred_model: 'claude-sonnet-4',
    examples: [
      'FastAPI 中如何实现 JWT 认证？',
      '如何设计数据库分库分表策略？',
    ],
  },
  {
    id: 'writing-assistant',
    name: '写作助手',
    type: 'writing',
    category: 'writing',
    description: '专注于各类文本写作、翻译、润色的智能助手',
    is_enabled: true,
    welcome: '你好！我是写作助手，可以帮你完成文章写作、翻译、润色等工作。告诉我你的写作需求吧！',
    preferred_model: 'claude-haiku-4',
    examples: [
      '帮我润色这段技术博客：...',
      '把这段英文翻译成中文：Hello, world!',
    ],
  },
]

/**
 * 根据 type 查找降级默认值。
 * 找不到时返回 undefined（调用方应做兜底处理）。
 */
export function getPromptDefault(type: string): PromptDefaultItem | undefined {
  return PROMPT_DEFAULTS.find((p) => p.type === type)
}

/**
 * 获取所有已启用的降级默认值。
 */
export function getEnabledPromptDefaults(): PromptDefaultItem[] {
  return PROMPT_DEFAULTS.filter((p) => p.is_enabled)
}