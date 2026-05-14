import { useEffect } from 'react'

function GlobalErrorHandler() {
  useEffect(() => {
    const handleError = (error: Error | Event) => {
      console.error('Global error:', error)
    }

    const handleWindowError = (
      message: string,
      _source?: string,
      _lineno?: number,
      _colno?: number,
      error?: Error
    ) => {
      handleError(error || new Error(message))
      return true
    }

    const handleUnhandledRejection = (event: PromiseRejectionEvent) => {
      handleError(event.reason)
    }

    window.onerror = handleWindowError as OnErrorEventHandler
    window.addEventListener('error', handleError)
    window.addEventListener('unhandledrejection', handleUnhandledRejection)

    return () => {
      window.onerror = null
      window.removeEventListener('error', handleError)
      window.removeEventListener('unhandledrejection', handleUnhandledRejection)
    }
  }, [])

  return null
}

export default GlobalErrorHandler