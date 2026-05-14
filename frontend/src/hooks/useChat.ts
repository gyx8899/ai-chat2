/**
 * 聊天核心 Hook，处理消息发送、流式响应、错误处理
 *
 * 功能特性：
 * - 支持 SSE 流式响应
 * - 消息重试机制
 * - 会话切换时自动终止当前流
 * - 支持图片附件上传
 */

import { useCallback, useRef, useEffect } from 'react'
import { useSearchParams } from 'next/navigation'
import { useChatStore } from '@/store/chatStore'
import { useSessionStore } from '@/store/sessionStore'
import { useModelStore } from '@/store/modelStore'
import { useTranslation } from '@/hooks/useTranslation'
import { streamSSE, SSEHttpError } from '@/lib/sseClient'
import type { ImageAttachment } from '@/types'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080'

export function useChat() {
  const loading = useChatStore((s) => s.loading)
  const ragHint = useChatStore((s) => s.ragHint)
  const { t } = useTranslation()
  const searchParams = useSearchParams()
  const promptId = searchParams.get('type') ?? ''

  const abortControllerRef = useRef<AbortController | null>(null)

  /** 组件卸载时统一中止当前流 */
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
        abortControllerRef.current = null
      }
    }
  }, [])

  /**
   * 发送消息的核心函数
   */
  const sendMessage = useCallback(
    async (query: string, overrideSessionId?: string, attachments?: ImageAttachment[]) => {
      const { setLoading, setRagHint, loading: currentLoading } = useChatStore.getState()
      const {
        activeSessionId: currentActive,
        addMessage,
        updateMessage,
        renameSession,
        sessions,
      } = useSessionStore.getState()

      const targetSessionId = overrideSessionId ?? currentActive
      if (!targetSessionId || currentLoading) return

      // 若已存在未完成 controller，先 abort 旧的再创建新的
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
        abortControllerRef.current = null
      }

      setLoading(true)
      setRagHint('')

      const controller = new AbortController()
      abortControllerRef.current = controller

      const userMsgId = crypto.randomUUID()
      const assistantMsgId = crypto.randomUUID()
      const now = Date.now()

      // 添加用户消息
      addMessage({
        id: userMsgId,
        role: 'user',
        content: query,
        createdAt: now,
        images: attachments?.map((a) => a.dataUrl).filter(Boolean) as string[],
      })

      // 会话标题默认以第一条用户消息内容为准（截断至 50 字符）
      const session = sessions.find((s) => s.id === targetSessionId)
      if (session && session.title === '新会话') {
        const title = query.slice(0, 50)
        renameSession(targetSessionId, title)
      }

      // 添加空白助手消息（用于流式填充）
      addMessage({
        id: assistantMsgId,
        role: 'assistant',
        content: '',
        createdAt: now + 1,
      })

      let contentBuffer = ''

      // 节流 flush：每 50ms 将 buffer 写入 UI
      let flushTimer: ReturnType<typeof setTimeout> | null = null
      const flushBuffer = () => {
        if (contentBuffer) {
          updateMessage(assistantMsgId, contentBuffer)
        }
      }
      const scheduleFlush = () => {
        if (flushTimer) return
        flushTimer = setTimeout(() => {
          flushBuffer()
          flushTimer = null
        }, 50)
      }
      const clearFlushTimer = () => {
        if (flushTimer) {
          clearTimeout(flushTimer)
          flushTimer = null
        }
      }

      // 获取当前选中的模型
      const currentModel = useModelStore.getState().current

      try {
        for await (const frame of streamSSE({
          url: `${API_BASE}/api/v1/chat/stream`,
          body: {
            query,
            session_id: targetSessionId,
            model: currentModel?.id,
            prompt_id: promptId || undefined,
          },
          signal: controller.signal,
        })) {
          // meta 帧：ragHint
          if ('meta' in frame) {
            if (frame.meta.ragHint) setRagHint(frame.meta.ragHint)
            continue
          }

          // error 帧
          if ('error' in frame) {
            clearFlushTimer()
            flushBuffer()
            updateMessage(assistantMsgId, contentBuffer + '\n\n[错误] ' + frame.error)
            break
          }

          // content 帧
          if ('content' in frame) {
            contentBuffer += frame.content
            scheduleFlush()
          }
        }

        // 正常结束：立即 flush 剩余 buffer
        clearFlushTimer()
        flushBuffer()
      } catch (err: unknown) {
        // AbortError：用户中止
        if (err instanceof Error && err.name === 'AbortError') {
          clearFlushTimer()
          contentBuffer = ''
          return
        }

        // HTTP 错误
        if (err instanceof SSEHttpError) {
          clearFlushTimer()
          flushBuffer()
          updateMessage(
            assistantMsgId,
            contentBuffer + '\n\n[错误] 请求失败（HTTP ' + err.status + '）'
          )
          return
        }

        // 网络错误
        console.warn('fetch /api/v1/chat/stream failed', err)
        clearFlushTimer()
        flushBuffer()
        updateMessage(assistantMsgId, contentBuffer + '\n\n[错误] ' + t('message.errorDefault'))
      } finally {
        clearFlushTimer()
        setLoading(false)
        abortControllerRef.current = null
      }
    },
    [t, promptId]
  )

  /** 停止当前正在进行的流式生成 */
  const stopGeneration = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      abortControllerRef.current = null
    }
  }, [])

  /** 重新生成最后一条助手回复 */
  const regenerate = useCallback(() => {
    const { activeSessionId: currentActive, activeMessages } = useSessionStore.getState()
    const { loading: currentLoading } = useChatStore.getState()
    if (!currentActive || currentLoading) return

    const lastUserMsg = [...activeMessages].reverse().find((m) => m.role === 'user')
    if (!lastUserMsg) return

    // 删除最后一条助手消息
    const lastAssistantIdx = [...activeMessages]
      .reverse()
      .findIndex((m) => m.role === 'assistant')
    if (lastAssistantIdx === -1) return

    const assistantIdx = activeMessages.length - 1 - lastAssistantIdx
    const newMessages = activeMessages.filter((_, i) => i !== assistantIdx)
    useSessionStore.getState().setActiveMessages(newMessages)

    setTimeout(() => sendMessage(lastUserMsg.content), 0)
  }, [sendMessage])

  /**
   * 发送消息的入口函数
   * 如果当前没有活跃会话，会自动创建一个新会话
   */
  const send = useCallback(
    async (text: string, attachments?: ImageAttachment[]) => {
      const { activeSessionId: currentActive, createSession } = useSessionStore.getState()
      if (currentActive) {
        sendMessage(text, undefined, attachments)
      } else {
        const newSession = await createSession()
        sendMessage(text, newSession.id, attachments)
      }
    },
    [sendMessage]
  )

  return { loading, ragHint, send, stopGeneration, regenerate }
}