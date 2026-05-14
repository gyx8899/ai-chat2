import { useEffect, useRef, useState } from 'react'

export interface UseShowHideOptions {
  defaultVisible?: boolean
  onShow?: () => void
  onHide?: () => void
}

export function useShowHide(options: UseShowHideOptions = {}): boolean {
  const { defaultVisible = true, onShow, onHide } = options

  const [isVisible, setIsVisible] = useState<boolean>(() => {
    if (typeof document === 'undefined') return defaultVisible
    return document.visibilityState !== 'hidden'
  })

  const onShowRef = useRef(onShow)
  const onHideRef = useRef(onHide)

  useEffect(() => {
    onShowRef.current = onShow
    onHideRef.current = onHide
  })

  useEffect(() => {
    if (typeof document === 'undefined') return

    const handleVisibilityChange = () => {
      const visible = document.visibilityState !== 'hidden'
      setIsVisible(visible)
      if (visible) {
        onShowRef.current?.()
      } else {
        onHideRef.current?.()
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange)
    }
  }, [])

  return isVisible
}