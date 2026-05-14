// Session Store - 基于原项目完整实现
import { create } from 'zustand'

// 消息类型
export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  model?: string
  images?: string[]
  reasoning?: string
  createdAt: number
  metadata?: Record<string, unknown>
}

// Session 类型
export interface Session {
  id: string
  title: string
  messages: Message[]
  createdAt: number
  updatedAt: number
  /** 该会话所属的提示词类型（来自后端 prompt_type 字段） */
  promptType?: string
  /** 是否仅本地创建（后端不可用时），跳过后端写操作 */
  localOnly?: boolean
}

export interface SessionState {
  // 当前会话
  currentSessionId: string | null
  activeSessionId: string | null
  activeMessages: Message[]
  sessions: Session[]
  isLoading: boolean
}

interface SessionActions {
  setCurrentSession: (sessionId: string | null) => void
  addMessage: (message: Message) => void
  updateMessage: (messageId: string, content: string) => void
  setActiveMessages: (messages: Message[]) => void
  setSessions: (sessions: Session[]) => void
  setLoading: (loading: boolean) => void
  clearCurrentSession: () => void
  createSession: (title?: string, promptType?: string) => Promise<Session>
  loadSessions: (promptType?: string) => Promise<void>
  renameSession: (sessionId: string, title: string) => Promise<void>
  deleteSession: (sessionId: string) => Promise<void>
  selectSession: (sessionId: string) => Promise<void>
}

type SessionStore = SessionState & SessionActions

export const useSessionStore = create<SessionStore>((set) => ({
  // 初始状态
  currentSessionId: null,
  activeSessionId: null,
  activeMessages: [],
  sessions: [],
  isLoading: false,
  // Actions
  setCurrentSession: (sessionId) => set({ currentSessionId: sessionId, activeSessionId: sessionId }),
  addMessage: (message) => set((state) => ({
    activeMessages: [...state.activeMessages, message]
  })),
  updateMessage: (messageId, content) => set((state) => ({
    activeMessages: state.activeMessages.map((msg) =>
      msg.id === messageId ? { ...msg, content } : msg
    )
  })),
  setActiveMessages: (messages) => set({ activeMessages: messages }),
  setSessions: (sessions) => set({ sessions }),
  setLoading: (loading) => set({ isLoading: loading }),
  clearCurrentSession: () => set({ currentSessionId: null, activeSessionId: null, activeMessages: [] }),
  createSession: async (title = '新会话', promptType) => {
    // 先调用后端 API 创建会话
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080'
    let serverSession: Session | null = null
    try {
      const controller = new AbortController()
      const timeout = setTimeout(() => controller.abort(), 5000)
      const res = await fetch(`${baseUrl}/api/v1/sessions/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, prompt_type: promptType }),
        signal: controller.signal,
      })
      clearTimeout(timeout)
      if (res.ok) {
        const data = await res.json()
        serverSession = {
          id: String(data.id),
          title: String(data.title),
          messages: [],
          createdAt: new Date(String(data.created_at)).getTime(),
          updatedAt: new Date(String(data.updated_at)).getTime(),
          promptType: data.prompt_type,
        }
      }
    } catch {
      // 后端不可用，使用本地 ID
    }

    const newSession: Session = serverSession ?? {
      id: `session-${Date.now()}`,
      title,
      messages: [],
      createdAt: Date.now(),
      updatedAt: Date.now(),
      promptType,
      localOnly: true,
    }

    set((state) => ({
      sessions: [newSession, ...state.sessions],
      currentSessionId: newSession.id,
      activeSessionId: newSession.id,
      activeMessages: [],
    }))
    return newSession
  },
  loadSessions: async (promptType?: string) => {
    set({ isLoading: true })
    const controller = new AbortController()
    const timer = setTimeout(() => controller.abort(), 5000)
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080'
      const url = promptType
        ? `${baseUrl}/api/v1/sessions/?prompt_type=${encodeURIComponent(promptType)}`
        : `${baseUrl}/api/v1/sessions/`
      const res = await fetch(url, { signal: controller.signal })
      clearTimeout(timer)
      if (!res.ok) throw new Error('Failed to load sessions')
      const data = await res.json()
      // 后端返回 { sessions: [...] }
      const sessions = (data.sessions || []).map((s: Record<string, unknown>) => ({
        id: String(s.id),
        title: String(s.title),
        messages: [],
        createdAt: new Date(String(s.created_at)).getTime(),
        updatedAt: new Date(String(s.updated_at)).getTime(),
        promptType: s.prompt_type as string | undefined,
        localOnly: false,
      }))
      set({ sessions })
    } catch (err) {
      clearTimeout(timer)
      // 超时或网络错误：静默返回空列表
      console.warn('[sessions] 加载会话失败，返回空列表', err instanceof Error ? err.message : err)
      set({ sessions: [] })
    } finally {
      set({ isLoading: false })
    }
  },
  renameSession: async (sessionId, title) => {
    // 仅更新本地状态，跳过后端 API（本地会话无后端 ID）
    const session = useSessionStore.getState().sessions.find(s => s.id === sessionId)
    if (session && !session.localOnly) {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080'
      const controller = new AbortController()
      const timer = setTimeout(() => controller.abort(), 5000)
      try {
        await fetch(`${baseUrl}/api/v1/sessions/${sessionId}`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ title }),
          signal: controller.signal,
        })
      } catch {
        // 静默失败，只更新本地状态
      } finally {
        clearTimeout(timer)
      }
    }
    set((state) => ({
      sessions: state.sessions.map((s) =>
        s.id === sessionId ? { ...s, title, updatedAt: Date.now() } : s
      ),
    }))
  },
  deleteSession: async (sessionId) => {
    // 仅更新本地状态，跳过后端 API（本地会话无后端 ID）
    const session = useSessionStore.getState().sessions.find(s => s.id === sessionId)
    if (session && !session.localOnly) {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080'
      const controller = new AbortController()
      const timer = setTimeout(() => controller.abort(), 5000)
      try {
        await fetch(`${baseUrl}/api/v1/sessions/${sessionId}`, {
          method: 'DELETE',
          signal: controller.signal,
        })
      } catch {
        // 静默失败，只更新本地状态
      } finally {
        clearTimeout(timer)
      }
    }
    set((state) => ({
      sessions: state.sessions.filter((s) => s.id !== sessionId),
      currentSessionId: state.currentSessionId === sessionId ? null : state.currentSessionId,
      activeSessionId: state.activeSessionId === sessionId ? null : state.activeSessionId,
      activeMessages: state.activeSessionId === sessionId ? [] : state.activeMessages,
    }))
  },
  selectSession: async (sessionId) => {
    // 从后端加载会话消息
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080'
    let messages: Message[] = []
    const controller = new AbortController()
    const timer = setTimeout(() => controller.abort(), 5000)
    try {
      const res = await fetch(
        `${baseUrl}/api/v1/sessions/${sessionId}/messages`,
        { signal: controller.signal }
      )
      clearTimeout(timer)
      if (res.ok) {
        const data = await res.json()
        messages = (data.messages || []).map((m: Record<string, unknown>) => ({
          id: String(m.id),
          role: String(m.role) as 'user' | 'assistant',
          content: String(m.content),
          createdAt: new Date(String(m.created_at)).getTime(),
          metadata: m.metadata as Record<string, unknown> | undefined,
        }))
      }
    } catch {
      clearTimeout(timer)
      // 静默失败，使用本地消息（messages 默认为 []）
    }

    set((state) => {
      // 合并后端消息到本地会话，保留 promptType
      const updatedSessions = state.sessions.map((s) =>
        s.id === sessionId ? { ...s, messages } : s
      )
      return {
        sessions: updatedSessions,
        currentSessionId: sessionId,
        activeSessionId: sessionId,
        activeMessages: messages,
      }
    })
  },
}))