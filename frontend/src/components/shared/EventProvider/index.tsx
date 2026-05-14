import React, { createContext, useContext, useEffect, useRef } from 'react'
import { EventBus } from '@/lib/EventBus'
import type { EventHandler } from '@/lib/EventBus'

// ─── Context ──────────────────────────────────────────────────────────────────
const EventContext = createContext<EventBus | null>(null)

// ─── Provider ─────────────────────────────────────────────────────────────────
export interface EventProviderProps {
  children: React.ReactNode
  bus?: EventBus
}

export function EventProvider({ children, bus }: EventProviderProps) {
  const [internalBus] = React.useState<EventBus | null>(() => (bus ? null : new EventBus()))
  const activeBus = bus ?? internalBus ?? DEFAULT_BUS

  useEffect(() => {
    if (bus || !internalBus) return undefined
    return () => {
      internalBus.off()
    }
  }, [bus, internalBus])

  return <EventContext.Provider value={activeBus}>{children}</EventContext.Provider>
}

// ─── useEvent ─────────────────────────────────────────────────────────────────
export function useEvent() {
  const bus = useContext(EventContext) ?? DEFAULT_BUS
  return bus
}

// ─── useEventListener ─────────────────────────────────────────────────────────
export function useEventListener(event: string, handler: EventHandler): void {
  const bus = useContext(EventContext) ?? DEFAULT_BUS
  const handlerRef = useRef(handler)

  useEffect(() => {
    handlerRef.current = handler
  })

  useEffect(() => {
    const stable = (...args: unknown[]) => handlerRef.current(...args)
    bus.on(event, stable)
    return () => {
      bus.off(event, stable)
    }
  }, [bus, event])
}

// ─── 降级默认实例 ─────────────────────────────────────────────────────────────
const DEFAULT_BUS = new EventBus()