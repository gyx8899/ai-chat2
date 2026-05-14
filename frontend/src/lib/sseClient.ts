/**
 * SSE 流消费器（async generator）
 *
 * 职责：fetch → 响应头校验 → ReadableStream 读取 → `\n\n` 分帧 →
 * `data:` 前缀剥离 → `[DONE]` 识别退出 → JSON 解析容错。
 */

export type SSEFrame =
  | { content: string }
  | { error: string }
  | { meta: { ragHint?: string } }

export interface StreamSSEOptions {
  url: string
  body: unknown
  signal?: AbortSignal
  headers?: Record<string, string>
}

/** HTTP 4xx/5xx 或非 ok 响应抛出的错误 */
export class SSEHttpError extends Error {
  status: number
  statusText: string
  body: string

  constructor(status: number, statusText: string, body: string) {
    super(`SSE HTTP ${status} ${statusText}: ${body}`)
    this.name = 'SSEHttpError'
    this.status = status
    this.statusText = statusText
    this.body = body
  }
}

const DONE_MARKER = '[DONE]'
const DATA_PREFIX = 'data:'

function parseFrame(raw: string): SSEFrame | null {
  try {
    const parsed: unknown = JSON.parse(raw)
    if (parsed && typeof parsed === 'object') {
      const obj = parsed as Record<string, unknown>
      if (typeof obj['content'] === 'string') {
        return { content: obj['content'] }
      }
      if (typeof obj['error'] === 'string') {
        return { error: obj['error'] }
      }
      if (obj['meta'] && typeof obj['meta'] === 'object') {
        const meta = obj['meta'] as Record<string, unknown>
        const ragHint =
          typeof meta['ragHint'] === 'string' ? meta['ragHint'] : undefined
        return { meta: { ragHint } }
      }
    }
    console.warn('[sseClient] unknown SSE frame shape, skipped', raw)
    return null
  } catch (err) {
    console.warn('[sseClient] SSE JSON parse error', raw, err)
    return null
  }
}

export async function* streamSSE(
  options: StreamSSEOptions
): AsyncGenerator<SSEFrame, void, void> {
  const { url, body, signal, headers } = options

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...headers,
    },
    body: JSON.stringify(body),
    signal,
  })

  if (!response.ok) {
    let errBody = ''
    try {
      errBody = await response.text()
    } catch {
      // ignore
    }
    throw new SSEHttpError(response.status, response.statusText, errBody)
  }

  if (!response.body) {
    throw new Error('SSE response has no body')
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  try {
    while (true) {
      const { value, done } = await reader.read()
      if (done) return

      buffer += decoder.decode(value, { stream: true })

      let sepIdx: number
      while ((sepIdx = buffer.indexOf('\n\n')) !== -1) {
        const part = buffer.slice(0, sepIdx)
        buffer = buffer.slice(sepIdx + 2)

        const trimmed = part.trim()
        if (!trimmed) continue
        if (!trimmed.startsWith(DATA_PREFIX)) {
          console.warn('[sseClient] SSE frame missing "data:" prefix, skipped', trimmed)
          continue
        }

        const payload = trimmed.slice(DATA_PREFIX.length).trim()
        if (payload === DONE_MARKER) return

        const frame = parseFrame(payload)
        if (frame) yield frame
      }
    }
  } finally {
    try {
      reader.releaseLock()
    } catch {
      // releaseLock 在 reader 已释放时会抛错，忽略
    }
  }
}