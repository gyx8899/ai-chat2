import { useCallback, useEffect, useRef } from 'react'

export function useTimeout() {
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const clear = useCallback(() => {
    if (timerRef.current !== null) {
      clearTimeout(timerRef.current)
      timerRef.current = null
    }
  }, [])

  const set = useCallback(
    (fn: () => void, delay: number) => {
      clear()
      if (delay >= 0) {
        timerRef.current = setTimeout(fn, delay)
      }
    },
    [clear]
  )

  useEffect(() => clear, [clear])

  return { set, clear }
}