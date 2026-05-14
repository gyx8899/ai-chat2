import { useCallback, useEffect, useRef } from 'react'

export interface UseClickCallbackOptions {
  delay?: number
  leading?: boolean
  trailing?: boolean
  stopPropagation?: boolean
}

export function useClickCallback<T extends (...args: Parameters<T>) => ReturnType<T>>(
  fn: T,
  deps: React.DependencyList,
  options: UseClickCallbackOptions = {}
): (...args: Parameters<T>) => void {
  const { delay = 1000, leading = true, trailing = false, stopPropagation = true } = options

  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const fnRef = useRef(fn)
  const depsRef = useRef(deps)
  const lastArgsRef = useRef<Parameters<T> | null>(null)
  const hasTrailingCallRef = useRef(false)
  const innerCleanupRef = useRef<(() => void) | null>(null)

  useEffect(() => {
    fnRef.current = fn
    depsRef.current = deps
  })

  const runInnerCleanup = useCallback(() => {
    if (typeof innerCleanupRef.current === 'function') {
      try {
        innerCleanupRef.current()
      } catch (e) {
        console.error('[useClickCallback] cleanup error:', e)
      }
      innerCleanupRef.current = null
    }
  }, [])

  useEffect(() => {
    return () => {
      if (timerRef.current !== null) {
        clearTimeout(timerRef.current)
        timerRef.current = null
      }
      runInnerCleanup()
      hasTrailingCallRef.current = false
      lastArgsRef.current = null
    }
  }, [runInnerCleanup])

  return useCallback(
    (...args: Parameters<T>) => {
      if (stopPropagation) {
        const event = (args as unknown[])[0] as Record<string, unknown> | undefined
        if (event && typeof event['stopPropagation'] === 'function') {
          ;(event['stopPropagation'] as () => void)()
        }
      }

      lastArgsRef.current = args

      if (timerRef.current === null) {
        const executeFn = (...execArgs: Parameters<T>) => {
          runInnerCleanup()
          const result = fnRef.current(...execArgs)
          if (typeof result === 'function') {
            innerCleanupRef.current = result as () => void
          }
        }

        if (leading) {
          executeFn(...args)
        } else if (trailing) {
          hasTrailingCallRef.current = true
        }

        timerRef.current = setTimeout(() => {
          timerRef.current = null
          if (trailing && hasTrailingCallRef.current && lastArgsRef.current) {
            executeFn(...(lastArgsRef.current as Parameters<T>))
            hasTrailingCallRef.current = false
            lastArgsRef.current = null
          }
        }, delay)
      } else {
        hasTrailingCallRef.current = true
      }
    },
    [delay, leading, trailing, stopPropagation, runInnerCleanup]
  )
}