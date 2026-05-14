'use client'

/**
 * PromptsContext — 管理当前页面提示词状态。
 *
 * 由 ChatPageClient 在外层提供。
 * 页面生命周期内 type 只读不变（由 URL query param 决定）。
 *
 * 提供内容：
 * - currentPrompt: 当前 URL type 对应的提示词配置（含 welcome/examples/preferred_model）
 * - isDegraded: 是否降级到本地 PROMPT_DEFAULTS（由 RSC 判断后传入）
 * - prompts: 全量提示词列表（用于 PromptSelector 渲染）
 * - getCurrentPrompt(type): 按 type 查询辅助函数
 */

import React, { createContext, useContext, useMemo } from 'react'
import type { PromptListItem } from '@/server/prompts'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface CurrentPrompt {
  /** 提示词 id */
  id: string
  /** 提示词 type */
  type: string
  /** 显示名称 */
  name: string
  /** 简短描述 */
  description: string
  /** 欢迎语 */
  welcome: string
  /** 示例问题列表 */
  examples: string[]
  /** 用户偏好的模型 id */
  preferred_model: string | undefined
}

export interface PromptsContextValue {
  /** 当前页面的提示词配置（必有值，不会 null） */
  currentPrompt: CurrentPrompt
  /** 是否处于降级状态（后端不可用） */
  isDegraded: boolean
  /** 全量提示词列表（不含 content） */
  prompts: PromptListItem[]
  /** 按 type 查询提示词 */
  getCurrentPrompt: (type: string) => CurrentPrompt | null
}

// ---------------------------------------------------------------------------
// Context
// ---------------------------------------------------------------------------

const PromptsCtx = createContext<PromptsContextValue | null>(null)

export function usePromptsContext(): PromptsContextValue {
  const ctx = useContext(PromptsCtx)
  if (!ctx) {
    throw new Error('usePromptsContext must be used inside <PromptsProvider>')
  }
  return ctx
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * 将 PromptListItem 转换为 CurrentPrompt 格式。
 * 缺失字段用占位值填充。
 */
function toCurrentPrompt(item: PromptListItem): CurrentPrompt {
  return {
    id: item.id,
    type: item.type,
    name: item.name,
    description: item.description ?? '',
    welcome: item.welcome ?? `你好！我是 ${item.name}，有什么可以帮你的吗？`,
    examples: item.examples ?? [],
    preferred_model: item.preferred_model,
  }
}

// ---------------------------------------------------------------------------
// Provider
// ---------------------------------------------------------------------------

interface PromptsProviderProps {
  children: React.ReactNode
  /** 当前页 URL type 参数 */
  currentType: string
  /** 从 RSC 加载的提示词列表（不含 content） */
  prompts: PromptListItem[]
  /** 是否降级（由 RSC server/prompts.ts 判断，后端不可用时为 true） */
  isDegraded?: boolean
}

export function PromptsProvider({
  children,
  currentType,
  prompts,
  isDegraded = false,
}: PromptsProviderProps) {
  // 构建 getCurrentPrompt 辅助函数
  const getCurrentPrompt = useMemo(() => {
    const map = new Map<string, CurrentPrompt>()
    for (const item of prompts) {
      map.set(item.type, toCurrentPrompt(item))
    }
    // 兜底：若 type 找不到，返回 null
    return (type: string): CurrentPrompt | null => {
      return map.get(type) ?? null
    }
  }, [prompts])

  // 当前页对应的提示词配置
  const currentPrompt = useMemo<CurrentPrompt>(() => {
    const found = getCurrentPrompt(currentType)
    if (found) return found
    // 理论上 RSC 会在 render 时处理 invalid type 重定向，此处是极端兜底
    return toCurrentPrompt({
      id: 'unknown',
      name: 'AI 助手',
      type: currentType,
      category: '',
      description: '',
      is_enabled: true,
    })
  }, [currentType, getCurrentPrompt])

  const value = useMemo<PromptsContextValue>(
    () => ({
      currentPrompt,
      isDegraded,
      prompts,
      getCurrentPrompt,
    }),
    [currentPrompt, isDegraded, prompts, getCurrentPrompt]
  )

  return <PromptsCtx.Provider value={value}>{children}</PromptsCtx.Provider>
}