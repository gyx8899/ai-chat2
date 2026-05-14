import { useCallback, useEffect, useRef } from 'react'

export function safeStringify(data: unknown): string | undefined {
  try {
    return JSON.stringify(data)
  } catch (error) {
    console.error('[safeStringify]', error)
    return undefined
  }
}

export function useDataChanged<T>(data?: T) {
  const snapshot = useRef<string | undefined>(undefined)

  useEffect(() => {
    if (data !== undefined) {
      snapshot.current = safeStringify(data)
    }
  }, [data])

  const checkDataChanged = useCallback((next: T): boolean => {
    const nextStr = safeStringify(next)

    if (nextStr === undefined) return false

    if (snapshot.current === undefined) {
      snapshot.current = nextStr
      return true
    }

    const changed = snapshot.current !== nextStr
    if (changed) snapshot.current = nextStr
    return changed
  }, [])

  return { checkDataChanged }
}