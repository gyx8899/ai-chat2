import React, { createContext, memo, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react'

// ─── Context ──────────────────────────────────────────────────────────────────
export interface PreloadContextType {
  setPreloadUrls: (urls: string[]) => void
}

const PreloadContext = createContext<PreloadContextType | null>(null)

// ─── Provider ─────────────────────────────────────────────────────────────────
export interface PreloadProviderProps {
  children: React.ReactNode
}

export const PreloadProvider = memo(({ children }: PreloadProviderProps) => {
  const [urls, setUrls] = useState<string[]>([])

  const setPreloadUrls = useCallback((newUrls: string[]) => {
    const unique = Array.from(new Set(newUrls.filter(Boolean)))
    setUrls(unique)
  }, [])

  const value = useMemo(() => ({ setPreloadUrls }), [setPreloadUrls])

  return (
    <PreloadContext.Provider value={value}>
      {children}
      <Preloader urls={urls} />
    </PreloadContext.Provider>
  )
})

PreloadProvider.displayName = 'PreloadProvider'

// ─── Preloader ────────────────────────────────────────────────────────────────
const Preloader = memo(({ urls }: { urls: string[] }) => {
  const loadedRef = useRef<Set<string>>(new Set())

  useEffect(() => {
    if (typeof window === 'undefined') return

    for (const url of urls) {
      if (loadedRef.current.has(url)) continue
      loadedRef.current.add(url)
      const img = new window.Image()
      img.src = url
    }
  }, [urls])

  return null
})

Preloader.displayName = 'Preloader'

// ─── usePreload ────────────────────────────────────────────────────────────────
export function usePreload(): PreloadContextType | null {
  return useContext(PreloadContext)
}