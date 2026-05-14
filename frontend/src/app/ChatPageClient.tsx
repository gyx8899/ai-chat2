'use client'

/**
 * ChatPageClient — 聊天页面的 Client Component 外壳。
 *
 * 由 RSC page.tsx 调用，包裹 PromptsProvider。
 * 负责：
 * 1. 提供 PromptsContext
 * 2. 包裹日志/事件 Provider
 * 3. 渲染主 UI（Sidebar + ChatArea + overlays）
 *
 * ⚠️ 不可 import 服务端模块（如 @/server/prompts）以外的服务器代码。
 */

import { Suspense } from 'react'
import { ChatArea } from '@/components/ChatArea'
import { Sidebar } from '@/components/Sidebar'
import { ToastContainer } from '@/components/ToastContainer'
import { TweaksPanel } from '@/components/TweaksPanel'
import { BackgroundLayer } from '@/components/BackgroundLayer'
import { EventProvider } from '@/components/shared/EventProvider'
import { LoggerProvider } from '@/components/shared/LoggerProvider'
import { PromptsProvider } from '@/contexts/PromptsContext'
import type { PromptListItem } from '@/server/prompts'

interface ChatPageClientProps {
  /** 当前页 URL type 参数 */
  currentType: string
  /** 从 RSC 加载的提示词列表（不含 content） */
  prompts: PromptListItem[]
  /** 是否降级（后端不可用时由 RSC 判断传入） */
  isDegraded?: boolean
}

function PageContent() {
  return (
    <div className="relative flex h-screen w-full overflow-hidden bg-background font-sans">
      {/* Background */}
      <BackgroundLayer />

      {/* Sidebar */}
      <Sidebar />

      {/* Main content */}
      <main className="relative flex flex-1 flex-col overflow-hidden">
        <ChatArea />
      </main>

      {/* Overlays */}
      <ToastContainer />
      <TweaksPanel />
    </div>
  )
}

export function ChatPageClient({ currentType, prompts, isDegraded }: ChatPageClientProps) {
  return (
    <LoggerProvider>
      <EventProvider>
        <PromptsProvider currentType={currentType} prompts={prompts} isDegraded={isDegraded}>
          {/* Suspense 兜底：useSearchParams 可能触发 pending 状态 */}
          <Suspense>
            <PageContent />
          </Suspense>
        </PromptsProvider>
      </EventProvider>
    </LoggerProvider>
  )
}