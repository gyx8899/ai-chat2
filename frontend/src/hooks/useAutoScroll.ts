import { useEffect, useRef } from 'react'

interface UseAutoScrollOptions {
  loading: boolean
  messageCount: number
  interval?: number
}

interface UseAutoScrollReturn {
  bottomRef: React.RefObject<HTMLDivElement | null>
  containerRef: React.RefObject<HTMLDivElement | null>
}

export function useAutoScroll({
  loading,
  messageCount,
  interval = 100,
}: UseAutoScrollOptions): UseAutoScrollReturn {
  const bottomRef = useRef<HTMLDivElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const userScrolledRef = useRef(false)

  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    const onWheel = (e: WheelEvent) => {
      if (loading && e.deltaY < 0) userScrolledRef.current = true
    }
    const onTouchMove = () => {
      if (loading) userScrolledRef.current = true
    }
    const onKeyDown = (e: KeyboardEvent) => {
      if (loading && (e.key === 'ArrowUp' || e.key === 'PageUp')) {
        userScrolledRef.current = true
      }
    }

    container.addEventListener('wheel', onWheel, { passive: true })
    container.addEventListener('touchmove', onTouchMove, { passive: true })
    container.addEventListener('keydown', onKeyDown)
    return () => {
      container.removeEventListener('wheel', onWheel)
      container.removeEventListener('touchmove', onTouchMove)
      container.removeEventListener('keydown', onKeyDown)
    }
  }, [loading])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messageCount])

  useEffect(() => {
    if (!loading) {
      if (!userScrolledRef.current) {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
      }
      userScrolledRef.current = false
      return
    }
    const id = setInterval(() => {
      if (userScrolledRef.current) return
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, interval)
    return () => clearInterval(id)
  }, [loading, interval])

  return { bottomRef, containerRef }
}