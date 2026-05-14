import { useEffect, useMemo, useRef, useState } from 'react'
import { useShowHide } from './useShowHide'

export type CountDownDate = Date | number | string | undefined

export interface CountDownOptions {
  targetDate?: CountDownDate
  interval?: number
  fillZero?: boolean
  onEnd?: () => void
}

export interface CountDownResult {
  days: string
  hours: string
  minutes: string
  seconds: string
}

function pad(num: number, fill: boolean): string {
  return fill && num < 10 ? `0${num}` : String(num)
}

function calcLeft(target?: CountDownDate): number {
  if (!target) return 0
  const left = new Date(target).getTime() - Date.now()
  return left > 0 ? left : 0
}

function parseMs(ms: number, fillZero: boolean): CountDownResult {
  return {
    days: pad(Math.floor(ms / 86_400_000), false),
    hours: pad(Math.floor(ms / 3_600_000) % 24, fillZero),
    minutes: pad(Math.floor(ms / 60_000) % 60, fillZero),
    seconds: pad(Math.floor(ms / 1_000) % 60, fillZero),
  }
}

export function getCountDownResult(target: CountDownDate, fillZero = false): CountDownResult {
  return parseMs(calcLeft(target), fillZero)
}

export function useCountDown(options?: CountDownOptions): readonly [number, CountDownResult] {
  const { targetDate, interval = 1000, fillZero = false, onEnd } = options ?? {}

  const [timeLeft, setTimeLeft] = useState(() => calcLeft(targetDate))
  const onEndRef = useRef(onEnd)

  useEffect(() => {
    onEndRef.current = onEnd
  })

  const isVisible = useShowHide()

  useEffect(() => {
    if (!targetDate) {
      const raf = requestAnimationFrame(() => setTimeLeft(0))
      return () => cancelAnimationFrame(raf)
    }

    if (!isVisible) return

    const left = calcLeft(targetDate)
    const raf = requestAnimationFrame(() => {
      setTimeLeft(left)
      if (left === 0) {
        onEndRef.current?.()
      }
    })

    if (left === 0) {
      return () => cancelAnimationFrame(raf)
    }

    const timer = setInterval(() => {
      const remaining = calcLeft(targetDate)
      setTimeLeft(remaining)
      if (remaining === 0) {
        clearInterval(timer)
        onEndRef.current?.()
      }
    }, interval)

    return () => {
      cancelAnimationFrame(raf)
      clearInterval(timer)
    }
  }, [targetDate, interval, isVisible])

  const formatted = useMemo(() => parseMs(timeLeft, fillZero), [timeLeft, fillZero])

  return [timeLeft, formatted] as const
}