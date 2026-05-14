// API 客户端 - 对接 backend
// Base URL from environment or default
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080/api'

export interface ApiResponse<T> {
  code: number
  message: string
  data: T
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  model?: string
  images?: string[]
  reasoning?: string
  createdAt: number
}

export interface Session {
  id: string
  title: string
  messages: ChatMessage[]
  createdAt: number
  updatedAt: number
}

export interface Model {
  id: string
  modelId: string
  name: string
  provider: string
  description?: string
}

class ApiClient {
  private baseUrl: string

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    })

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`)
    }

    return response.json()
  }

  // 会话相关
  async getSessions(): Promise<ApiResponse<Session[]>> {
    return this.request<Session[]>('/sessions')
  }

  async getSession(id: string): Promise<ApiResponse<Session>> {
    return this.request<Session>(`/sessions/${id}`)
  }

  async createSession(title?: string): Promise<ApiResponse<Session>> {
    return this.request<Session>('/sessions', {
      method: 'POST',
      body: JSON.stringify({ title }),
    })
  }

  async deleteSession(id: string): Promise<ApiResponse<void>> {
    return this.request<void>(`/sessions/${id}`, {
      method: 'DELETE',
    })
  }

  // 聊天相关
  async sendMessage(
    content: string,
    modelId?: string,
    sessionId?: string,
    images?: string[]
  ): Promise<ApiResponse<ChatMessage>> {
    return this.request<ChatMessage>('/chat', {
      method: 'POST',
      body: JSON.stringify({
        content,
        modelId,
        sessionId,
        images,
      }),
    })
  }

  // 流式聊天
  async *streamChat(
    content: string,
    modelId?: string,
    sessionId?: string,
    images?: string[]
  ): AsyncGenerator<{ content?: string; done: boolean; error?: string }> {
    const response = await fetch(`${this.baseUrl}/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        content,
        modelId,
        sessionId,
        images,
      }),
    })

    if (!response.ok) {
      throw new Error(`Stream Error: ${response.status} ${response.statusText}`)
    }

    const reader = response.body?.getReader()
    if (!reader) {
      throw new Error('Response body is not readable')
    }

    const decoder = new TextDecoder()
    let buffer = ''

    try {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              yield data
            } catch {
              // Skip invalid JSON
            }
          }
        }
      }
    } finally {
      reader.releaseLock()
    }
  }

  // 模型相关
  async getModels(): Promise<ApiResponse<Model[]>> {
    return this.request<Model[]>('/models')
  }
}

export const apiClient = new ApiClient(API_BASE_URL)