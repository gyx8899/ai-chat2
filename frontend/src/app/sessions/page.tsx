'use client'

import { Sidebar } from '@/components/Sidebar'
import { ChatArea } from '@/components/ChatArea'
import { ToastContainer } from '@/components/ToastContainer'
import { TweaksPanel } from '@/components/TweaksPanel'
import { EventProvider } from '@/components/shared/EventProvider'
import { LoggerProvider } from '@/components/shared/LoggerProvider'

export default function SessionsPage() {
  return (
    <LoggerProvider>
      <EventProvider>
        <div className="relative flex h-screen w-full overflow-hidden bg-background font-sans">
          {/* Sidebar */}
          <Sidebar />

          {/* Main content - 显示会话列表或聊天区域 */}
          <main className="relative flex flex-1 flex-col overflow-hidden">
            <ChatArea />
          </main>

          {/* Overlays */}
          <ToastContainer />
          <TweaksPanel />
        </div>
      </EventProvider>
    </LoggerProvider>
  )
}