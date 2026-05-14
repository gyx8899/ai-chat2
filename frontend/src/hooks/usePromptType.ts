'use client'

/**
 * usePromptType — 从 URL 读取并校验 type 参数。
 *
 * 职责：
 * 1. 读取 `?type=` query param
 * 2. 若 URL 无 type 参数，将 `default_type` 写回 URL（replace）
 * 3. 若 URL type 非法（不在 prompts 列表中），触发重定向到默认 type
 *
 * 仅在 Client Component 中使用。
 * 页面初次渲染由 RSC 处理 invalid type 重定向，此 hook 处理运行时边界。
 */

import { useEffect, useRef } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import type { PromptListItem } from '@/server/prompts'

interface UsePromptTypeOptions {
  /** 全量提示词列表（不含 content） */
  prompts: PromptListItem[]
  /** 默认提示词 type（来自后端） */
  defaultType: string
}

/**
 * 监听 URL type 参数，做运行时兜底同步。
 *
 * 触发条件：
 * - component mount 时 URL 无 `type` param
 * - component mount 时 URL `type` 不在 prompts 列表中
 *
 * @param options.prompts      提示词列表
 * @param options.defaultType  默认 type（RSC 从后端获取）
 */
export function usePromptType({ prompts, defaultType }: UsePromptTypeOptions) {
  const router = useRouter()
  const searchParams = useSearchParams()
  const currentType = searchParams.get('type') ?? ''
  const mounted = useRef(false)

  useEffect(() => {
    if (!mounted.current) {
      mounted.current = true
      return
    }

    const validTypes = new Set(prompts.map((p) => p.type))
    const target = defaultType

    if (!currentType) {
      // URL 无 type，写回 default_type
      const params = new URLSearchParams(searchParams.toString())
      params.set('type', target)
      router.replace(`?${params.toString()}`, { scroll: false })
      return
    }

    if (!validTypes.has(currentType)) {
      // type 非法，重定向到 default_type
      const params = new URLSearchParams(searchParams.toString())
      params.set('type', target)
      router.replace(`?${params.toString()}`, { scroll: false })
    }
  }, [currentType, prompts, defaultType, router, searchParams])

  return currentType || defaultType
}