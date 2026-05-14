/**
 * EventBus - 轻量级事件总线，带重放缓存机制
 */
export type EventHandler = (...args: unknown[]) => void

export class EventBus {
  private _events: Record<string, EventHandler[]> = {}
  private _buffer: Record<string, unknown[]> = {}

  on(event: string, handler: EventHandler): this {
    if (typeof handler !== 'function') return this
    ;(this._events[event] || (this._events[event] = [])).push(handler)

    const buffered = this._buffer[event]
    if (buffered) {
      try {
        handler(...buffered)
      } catch (e) {
        console.error('[EventBus] replay error:', e)
      }
      delete this._buffer[event]
    }

    return this
  }

  once(event: string, handler: EventHandler): this {
    if (typeof handler !== 'function') return this

    const wrapper = (...args: unknown[]) => {
      this.off(event, wrapper)
      handler(...args)
    }
    return this.on(event, wrapper)
  }

  off(event?: string, handler?: EventHandler): this {
    if (!event) {
      this._events = {}
      this._buffer = {}
      return this
    }

    const handlers = this._events[event]
    if (!handlers) return this

    if (!handler) {
      delete this._events[event]
      delete this._buffer[event]
      return this
    }

    const index = handlers.indexOf(handler)
    if (index > -1) {
      handlers.splice(index, 1)
      if (!handlers.length) {
        delete this._events[event]
        delete this._buffer[event]
      }
    }

    return this
  }

  emit(event: string, ...args: unknown[]): this {
    const handlers = this._events[event]

    if (!handlers?.length) {
      this._buffer[event] = args
      return this
    }

    const callbacks = handlers.slice()
    for (let i = 0; i < callbacks.length; i++) {
      try {
        callbacks[i](...args)
      } catch (e) {
        console.error('[EventBus] emit error:', e)
      }
    }

    return this
  }
}