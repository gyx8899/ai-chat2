'use client'

import { useEffect } from 'react'
import { useUIStore } from '@/store/uiStore'

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const isDark = useUIStore((s) => s.isDark)

  useEffect(() => {
    const root = document.documentElement
    if (isDark) {
      root.classList.add('dark')
    } else {
      root.classList.remove('dark')
    }
  }, [isDark])

  return <>{children}</>
}