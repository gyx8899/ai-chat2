import React, { createContext, useContext, useMemo, useState } from 'react'
import { Logger } from '@/lib/Logger'
import type { LoggerOptions, LogLevelName } from '@/lib/Logger'

// ─── Context ──────────────────────────────────────────────────────────────────
const LoggerContext = createContext<Logger | null>(null)

// ─── Provider ─────────────────────────────────────────────────────────────────
export interface LoggerProviderProps {
  children: React.ReactNode
  prefix?: string
  level?: LogLevelName
  timestamp?: boolean
  transports?: LoggerOptions['transports']
}

export function LoggerProvider({
  children,
  prefix,
  level,
  timestamp,
  transports,
}: LoggerProviderProps) {
  const [transportsSnapshot] = useState(transports)

  const loggerInstance = useMemo(
    () =>
      new Logger({
        prefix,
        level,
        timestamp,
        transports: transportsSnapshot,
      }),
    [prefix, level, timestamp, transportsSnapshot]
  )

  return <LoggerContext.Provider value={loggerInstance}>{children}</LoggerContext.Provider>
}

// ─── useLogger ────────────────────────────────────────────────────────────────
export function useLogger(childPrefix?: string): Logger {
  const ctx = useContext(LoggerContext)
  const base = ctx ?? DEFAULT_LOGGER

  return useMemo(() => {
    if (childPrefix !== undefined) {
      return base.child({ prefix: childPrefix })
    }
    return base
  }, [base, childPrefix])
}

// ─── 降级默认实例 ─────────────────────────────────────────────────────────────
const DEFAULT_LOGGER = new Logger()