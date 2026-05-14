'use client'

import { ChevronDown, Check, AlertTriangle } from 'lucide-react'
import { usePathname, useSearchParams } from 'next/navigation'
import { usePromptsContext } from '@/contexts/PromptsContext'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { cn } from '@/lib/utils'

/**
 * 降级 Banner — 后端不可用时显示警告。
 * 固定在页面顶部，不遮挡主内容。
 */
function DegradedBanner() {
  return (
    <div
      className="flex items-center gap-2 px-4 py-2 text-xs font-medium bg-amber-50 dark:bg-amber-950/30 border-b border-amber-200 dark:border-amber-800 text-amber-700 dark:text-amber-400"
      role="alert"
    >
      <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
      <span>提示词配置降级使用本地默认值，后端连接已断开</span>
    </div>
  )
}

export function PromptSelector() {
  const pathname = usePathname()
  const searchParams = useSearchParams()
  const { currentPrompt, prompts, isDegraded } = usePromptsContext()

  const currentType = searchParams.get('type') ?? ''

  const handleSwitch = (type: string) => {
    // 切换提示词：打开新的浏览器标签页，原页面不变
    const params = new URLSearchParams(searchParams.toString())
    params.set('type', type)
    window.open(`${pathname}?${params.toString()}`, '_blank', 'noopener,noreferrer')
  }

  return (
    <>
      {isDegraded && <DegradedBanner />}
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            variant="outline"
            size="sm"
            className="group h-9 gap-1.5 rounded-full border-border/60 bg-background/60 px-2.5 text-xs font-medium text-foreground hover:bg-background hover:shadow-glow transition-all"
            aria-label="切换提示词"
          >
            <span
              className="inline-block h-1.5 w-1.5 rounded-full shrink-0"
              style={{
                backgroundColor: isDegraded
                  ? 'var(--warning, #f59e0b)'
                  : 'var(--primary-oklch)',
                boxShadow: isDegraded
                  ? '0 0 6px #f59e0b'
                  : '0 0 6px var(--primary-glow)',
              }}
              aria-hidden
            />
            <span className="max-w-[80px] sm:max-w-[120px] truncate">
              {currentPrompt.name}
            </span>
            <ChevronDown className="w-3 h-3 text-muted-foreground transition-transform group-data-[state=open]:rotate-180" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent
          align="end"
          sideOffset={8}
          className="w-72 max-h-80 overflow-y-auto rounded-lg border-border/60 bg-popover/95 backdrop-blur-xl shadow-glow"
        >
          <DropdownMenuLabel className="font-display text-xs font-medium uppercase tracking-wider text-muted-foreground">
            选择助手
          </DropdownMenuLabel>
          <DropdownMenuSeparator />
          {prompts.map((prompt) => {
            const isActive = prompt.type === currentType
            return (
              <DropdownMenuItem
                key={prompt.type}
                onSelect={() => !isActive && handleSwitch(prompt.type)}
                className={cn(
                  'items-start gap-2.5 px-3 py-2.5 rounded-md cursor-pointer focus:bg-accent',
                  isActive && 'bg-accent text-accent-foreground cursor-default',
                )}
                aria-current={isActive ? 'true' : undefined}
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1">
                    <span className="text-xs font-medium truncate">{prompt.name}</span>
                    {isActive ? (
                      <Check
                        className="w-3 h-3 shrink-0"
                        style={{ color: 'var(--primary-oklch)' }}
                      />
                    ) : (
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-muted text-muted-foreground shrink-0">
                        新标签
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground mt-0.5 line-clamp-2">
                    {prompt.description}
                  </p>
                  {isActive && (
                    <span className="text-[10px] mt-1 inline-block text-muted-foreground/60">
                      当前页
                    </span>
                  )}
                </div>
              </DropdownMenuItem>
            )
          })}
        </DropdownMenuContent>
      </DropdownMenu>
    </>
  )
}