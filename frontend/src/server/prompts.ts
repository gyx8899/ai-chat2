/**
 * 服务端提示词加载模块（RSC 专用）。
 *
 * 仅在服务端执行——不可 import 到 Client Component。
 *
 * 功能：
 * 1. 从后端 API 加载提示词列表（含 welcome / preferred_model / examples）
 * 2. 后端不可用时降级到 PROMPT_DEFAULTS（静默 warn，不抛错）
 * 3. 提供 revalidateTag("prompts") 供 Webhook 调用以热更新缓存
 *
 * Next.js 数据缓存策略：
 *   - revalidateTag("prompts")  → POST /api/v1/config/prompts/reload 后端触发
 *   - 后端 reload 后下一次 SSR 请求会重新 fetch，确保 RSC 直出的菜单数据是最新的
 */

import { revalidateTag } from 'next/cache'
import {
  PROMPT_DEFAULTS,
  getPromptDefault,
  type PromptDefaultItem,
} from '@/lib/promptDefaults'

/** 后端 list 接口返回的数据结构（不含 content） */
export interface PromptListItem {
  id: string
  name: string
  type: string
  category: string
  description: string
  is_enabled: boolean
  /** 欢迎语 */
  welcome?: string
  /** 偏好模型 */
  preferred_model?: string
  /** 示例问题列表（仅 question，answer 不下发到前端）。 */
  examples?: string[]
}

const CACHE_TAG = 'prompts'
const REQUEST_TIMEOUT_MS = 3000

/**
 * 从后端加载提示词列表。
 * 失败时静默降级到 PROMPT_DEFAULTS。
 *
 * @param backendUrl  后端内部 URL（如 http://backend:8080）
 * @returns [prompts, isDegraded] — isDegraded=true 表示使用了降级默认值
 */
async function fetchFromBackend(
  backendUrl: string
): Promise<[prompts: PromptListItem[], isDegraded: boolean]> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS)

  try {
    const res = await fetch(`${backendUrl}/api/v1/config/prompts/list`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
      signal: controller.signal,
      // Next.js 强制服务端缓存——由 revalidateTag("prompts") 控制失效
      next: { tags: [CACHE_TAG] },
    })

    clearTimeout(timer)

    if (!res.ok) {
      console.warn(
        `[prompts] 后端返回非 200 (${res.status})，使用降级默认值`
      )
      return [PROMPT_DEFAULTS as PromptListItem[], true]
    }

    const json = (await res.json()) as { data?: PromptListItem[] }

    if (!Array.isArray(json.data)) {
      console.warn('[prompts] 后端响应格式异常，使用降级默认值')
      return [PROMPT_DEFAULTS as PromptListItem[], true]
    }

    // 后端正常返回
    return [json.data, false]
  } catch (err) {
    clearTimeout(timer)

    if (err instanceof Error && err.name === 'AbortError') {
      console.warn('[prompts] 后端请求超时，使用降级默认值')
    } else {
      console.warn('[prompts] 后端请求失败，使用降级默认值', err)
    }

    return [PROMPT_DEFAULTS as PromptListItem[], true]
  }
}

/**
 * 加载提示词列表（供 RSC 调用）。
 *
 * 保证返回值不为 null——后端不可用时返回 PROMPT_DEFAULTS。
 *
 * @returns [prompts, isDegraded]  — isDegraded 为 true 表示使用了降级数据
 */
export async function getPrompts(): Promise<
  [prompts: PromptListItem[], isDegraded: boolean]
> {
  const backendUrl = process.env.BACKEND_INTERNAL_URL

  if (!backendUrl) {
    console.warn('[prompts] BACKEND_INTERNAL_URL 未配置，使用降级默认值')
    return [PROMPT_DEFAULTS as PromptListItem[], true]
  }

  return fetchFromBackend(backendUrl)
}

/**
 * 根据 type 获取单条提示词。
 * 后端不可用时使用 getPromptDefault(type) 降级。
 */
export async function getPromptByType(
  type: string
): Promise<PromptListItem | PromptDefaultItem | undefined> {
  const [prompts] = await getPrompts()
  return prompts.find((p) => p.type === type) ?? getPromptDefault(type)
}

/**
 * 获取所有已启用的提示词。
 */
export async function getEnabledPrompts(): Promise<PromptListItem[]> {
  const [prompts] = await getPrompts()
  return prompts.filter((p) => p.is_enabled)
}

/**
 * 热更新：通知 Next.js 清除 prompts 缓存。
 * 供 reload Webhook 端点调用（见 router/prompts.ts POST /reload）。
 *
 * 注意：此函数在 Webhook handler 中调用，仅在服务端运行。
 */
export function invalidatePromptsCache(): void {
  revalidateTag(CACHE_TAG)
}