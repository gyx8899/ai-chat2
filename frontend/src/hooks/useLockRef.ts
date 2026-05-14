import { useCallback } from 'react'
import { useStateRef } from './useStateRef'
import { useTimeout } from './useTimeout'

export interface UseLockOptions {
  unLockDelay?: number
}

export function useLockRef(options: UseLockOptions = {}) {
  const { unLockDelay = 1000 } = options

  const [, setIsLocked, lockedRef] = useStateRef(false)
  const timer = useTimeout()

  const setLocked = useCallback(
    (locked: boolean) => {
      setIsLocked(locked)
      if (locked) {
        timer.set(() => setIsLocked(false), unLockDelay)
      } else {
        timer.clear()
      }
    },
    [setIsLocked, timer, unLockDelay]
  )

  return [lockedRef, setLocked] as const
}