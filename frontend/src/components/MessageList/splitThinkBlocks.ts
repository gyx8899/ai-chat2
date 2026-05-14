/**
 * Think 块解析：将助手消息内容按 `<think>...</think>` 切分为段。
 *
 * 设计要点：
 * - 流式期间未闭合的 `<think>` 也能识别（closed=false），以便渲染加载态
 * - normal 段保留原始文本（含前后空白），交给 Markdown 渲染层处理
 * - 不消费内嵌的 `<think>` 嵌套（业务上 deepseek-r1 不会嵌套，简单实现优先）
 */
export type ContentSegment =
  | { type: 'normal'; text: string }
  | { type: 'think'; text: string; closed: boolean }

const THINK_PATTERN = /<think>([\s\S]*?)(<\/think>|$)/g

export function splitThinkBlocks(content: string): ContentSegment[] {
  if (!content) return []

  const segments: ContentSegment[] = []
  let lastIndex = 0
  let match: RegExpExecArray | null

  // 重置 regex lastIndex（避免外部共享状态污染）
  THINK_PATTERN.lastIndex = 0

  while ((match = THINK_PATTERN.exec(content)) !== null) {
    if (match.index > lastIndex) {
      segments.push({ type: 'normal', text: content.slice(lastIndex, match.index) })
    }
    segments.push({
      type: 'think',
      text: match[1],
      closed: match[2] === '</think>',
    })
    lastIndex = THINK_PATTERN.lastIndex

    // 防止零长度匹配导致死循环（理论上 `<think></think>` 即 match[1]='' 时 lastIndex 会推进）
    if (match.index === THINK_PATTERN.lastIndex) {
      THINK_PATTERN.lastIndex++
    }
  }

  if (lastIndex < content.length) {
    segments.push({ type: 'normal', text: content.slice(lastIndex) })
  }

  // 边界：完全无 think 标签时，整段作为 normal 返回
  if (segments.length === 0) {
    segments.push({ type: 'normal', text: content })
  }

  return segments
}
