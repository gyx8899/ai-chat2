// ─── 日志级别 ─────────────────────────────────────────────────────────────────
export const LogLevel = {
  debug: 0,
  info: 1,
  warn: 2,
  error: 3,
  silent: 4,
} as const

export type LogLevelName = keyof typeof LogLevel

// ─── Transport ────────────────────────────────────────────────────────────────
export interface LogEntry {
  level: LogLevelName
  prefix: string
  message: string
  args: unknown[]
  timestamp: Date
}

export type LogTransport = (entry: LogEntry) => void

// ─── LoggerProxy ──────────────────────────────────────────────────────────────
export interface LoggerProxy {
  debug(message: string, ...args: unknown[]): void
  info(message: string, ...args: unknown[]): void
  warn(message: string, ...args: unknown[]): void
  error(message: string, ...args: unknown[]): void
}

// ─── 配置 ─────────────────────────────────────────────────────────────────────
export interface LoggerOptions {
  prefix?: string
  level?: LogLevelName
  timestamp?: boolean
  transports?: LogTransport[]
}

// ─── Logger 类 ────────────────────────────────────────────────────────────────
export class Logger {
  private readonly prefix: string
  private readonly showTimestamp: boolean
  private readonly transports: LogTransport[]
  private minLevel: number

  constructor(options: LoggerOptions = {}) {
    const { prefix = '', level, timestamp = false, transports = [] } = options

    this.prefix = prefix
    this.showTimestamp = timestamp
    this.transports = transports

    const proc = (globalThis as Record<string, unknown>)['process'] as
      | { env?: Record<string, unknown> }
      | undefined
    const isProd = proc?.env?.['NODE_ENV'] === 'production'
    const defaultLevel: LogLevelName = isProd ? 'warn' : 'debug'
    this.minLevel = LogLevel[level ?? defaultLevel]
  }

  setLevel(level: LogLevelName): void {
    this.minLevel = LogLevel[level]
  }

  getLevel(): LogLevelName {
    const entry = Object.entries(LogLevel).find(([, v]) => v === this.minLevel)
    return (entry?.[0] ?? 'debug') as LogLevelName
  }

  debug(message: string, ...args: unknown[]): void {
    this._log('debug', message, args)
  }

  info(message: string, ...args: unknown[]): void {
    this._log('info', message, args)
  }

  warn(message: string, ...args: unknown[]): void {
    this._log('warn', message, args)
  }

  error(message: string, ...args: unknown[]): void {
    this._log('error', message, args)
  }

  child(overrides: Pick<LoggerOptions, 'prefix' | 'level'>): Logger {
    return new Logger({
      prefix: overrides.prefix ?? this.prefix,
      level: overrides.level ?? this.getLevel(),
      timestamp: this.showTimestamp,
      transports: this.transports,
    })
  }

  withPrefix(prefix: string): LoggerProxy {
    return {
      debug: (message, ...args) => this._logWithPrefix('debug', prefix, message, args),
      info: (message, ...args) => this._logWithPrefix('info', prefix, message, args),
      warn: (message, ...args) => this._logWithPrefix('warn', prefix, message, args),
      error: (message, ...args) => this._logWithPrefix('error', prefix, message, args),
    }
  }

  private _log(level: LogLevelName, message: string, args: unknown[]): void {
    this._logWithPrefix(level, this.prefix, message, args)
  }

  private _logWithPrefix(
    level: LogLevelName,
    prefix: string,
    message: string,
    args: unknown[]
  ): void {
    if (LogLevel[level] < this.minLevel) return

    const entry: LogEntry = {
      level,
      prefix,
      message,
      args,
      timestamp: new Date(),
    }

    const parts: unknown[] = []
    if (this.showTimestamp) parts.push(`[${entry.timestamp.toISOString()}]`)
    if (prefix) parts.push(prefix)
    parts.push(message)
    if (args.length > 0) parts.push(...args)

    const consoleFn = CONSOLE_MAP[level]
    consoleFn(...parts)

    for (const transport of this.transports) {
      try {
        transport(entry)
      } catch (e) {
        console.error('[Logger] transport error:', e)
      }
    }
  }
}

// ─── 控制台方法映射 ───────────────────────────────────────────────────────────
const CONSOLE_MAP: Record<LogLevelName, (...args: unknown[]) => void> = {
  debug: console.debug.bind(console),
  info: console.info.bind(console),
  warn: console.warn.bind(console),
  error: console.error.bind(console),
  silent: () => {},
}

// ─── 默认单例 ────────────────────────────────────────────────────────────────
export const logger = new Logger()