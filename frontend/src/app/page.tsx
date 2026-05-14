import type { Metadata } from 'next'
import { redirect } from 'next/navigation'
import { getPrompts } from '@/server/prompts'
import { ChatPageClient } from './ChatPageClient'

interface HomePageProps {
  searchParams: Promise<{ type?: string }>
}

/**
 * 首页 — Server Component（SSR 直出）。
 *
 * 职责：
 * 1. 读取 `?type=` 参数
 * 2. 从后端加载提示词列表（含 welcome/examples/preferred_model，不含 content）
 * 3. 无效 type → redirect 到 `?type=${default_type}`
 * 4. 生成 metadata（tab 标题）
 * 5. 将 prompts + currentType 传给 ChatPageClient
 *
 * 安全设计：服务端直出不含 content 的菜单数据，浏览器 Network 不暴露完整提示词。
 */
export async function generateMetadata(_props: HomePageProps): Promise<Metadata> {
  return { title: 'AI Chat' }
}

export default async function HomePage({ searchParams }: HomePageProps) {
  const params = await searchParams
  const typeParam = params.type

  // 加载提示词列表并获取降级状态
  const [prompts, isDegraded] = await getPrompts()

  // 找出 default_type（prompts.json 中标记 is_default: true 的项）
  const defaultPrompt = prompts.find((p) => p.is_enabled) ?? prompts[0]
  const defaultType = defaultPrompt?.type ?? 'default'

  // 校验 type 参数：无效时重定向到 default_type
  if (typeParam === undefined) {
    redirect(`/?type=${defaultType}`)
  }

  const validTypes = new Set(prompts.map((p) => p.type))
  if (!validTypes.has(typeParam)) {
    redirect(`/?type=${defaultType}`)
  }

  return <ChatPageClient currentType={typeParam} prompts={prompts} isDegraded={isDegraded} />
}