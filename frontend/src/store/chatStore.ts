// 聊天 Store - 基于原项目完整实现
import { create } from 'zustand'

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  createdAt?: Date
}

interface ChatState {
  messages: Message[]
  isStreaming: boolean
  loading: boolean
  ragHint: string
}

interface ChatActions {
  addMessage: (message: Message) => void
  setStreaming: (streaming: boolean) => void
  setLoading: (loading: boolean) => void
  clearMessages: () => void
  setRagHint: (hint: string) => void
}

type ChatStore = ChatState & ChatActions

export const useChatStore = create<ChatStore>((set) => ({
  messages: [],
  isStreaming: false,
  loading: false,
  ragHint: '',
  addMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),
  setStreaming: (streaming) => set({ isStreaming: streaming }),
  setLoading: (loading) => set({ loading }),
  clearMessages: () => set({ messages: [] }),
  setRagHint: (hint) => set({ ragHint: hint }),
}))