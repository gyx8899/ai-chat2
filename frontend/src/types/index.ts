// 类型定义模块

// 消息类型
export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  model?: string
  images?: string[]
  attachments?: ImageAttachment[]
  reasoning?: string
  ragHint?: string
  isError?: boolean
  errorText?: string
  createdAt: number
  /** 消息元数据（如 prompt_id、model_id），来自 assistant 消息 */
  metadata?: Record<string, unknown>
}

// 图片附件
export interface ImageAttachment {
  id: string
  url?: string
  dataUrl?: string // base64 图片数据
  name?: string
  size?: number
}

// 消息内容类型
export type MessageContent = string | (string | ImageAttachment)[]

// API 响应
export interface ApiResponse<T = unknown> {
  code: number
  message: string
  data: T
}

// 分页响应
export interface PaginatedResponse<T> extends ApiResponse<T[]> {
  total: number
  page: number
  pageSize: number
}

// 流式响应事件
export interface StreamEvent {
  type: 'message' | 'error' | 'done'
  content?: string
  reasoning?: string
  error?: string
}