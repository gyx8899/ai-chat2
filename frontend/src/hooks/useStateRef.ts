import { useCallback, useRef, useState } from 'react'

type Dispatch<T> = (action: T | ((prev: T) => T)) => void

export function useStateRef<T>(initial: T): [T, Dispatch<T>, React.RefObject<T>] {
  const [state, setState] = useState<T>(initial)
  const ref = useRef<T>(state)

  const dispatch = useCallback<Dispatch<T>>(action => {
    const next = typeof action === 'function' ? (action as (prev: T) => T)(ref.current) : action
    if (ref.current === next) return
    ref.current = next
    setState(next)
  }, [])

  return [state, dispatch, ref]
}