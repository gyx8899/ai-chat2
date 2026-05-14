/**
 * Revalidate Webhook — 热更新提示词缓存。
 *
 * 触发流程：
 * 1. 后端 POST /api/v1/config/prompts/reload 成功后
 * 2. 后端调用此端点（`process.env.FRONTEND_URL/api/revalidate-prompts?secret=...`）
 * 3. 本端点验证 secret 后调用 revalidateTag("prompts")
 * 4. Next.js 清除服务端 prompts 缓存，下一次 SSR 请求会重新 fetch 后端
 *
 * 安全：仅验证 secret，不做其他操作。
 */

import { NextRequest, NextResponse } from 'next/server'
import { revalidateTag } from 'next/cache'

export async function POST(request: NextRequest) {
  const secret = request.nextUrl.searchParams.get('secret')

  // 校验 secret
  const expectedSecret = process.env.REVALIDATE_SECRET
  if (!expectedSecret || secret !== expectedSecret) {
    return NextResponse.json(
      { error: 'Unauthorized' },
      { status: 401 }
    )
  }

  try {
    // 清除 Next.js 服务端 prompts 缓存
    revalidateTag('prompts')
    return NextResponse.json({ revalidated: true, timestamp: Date.now() })
  } catch (err) {
    console.error('[revalidate-prompts] revalidateTag failed', err)
    return NextResponse.json(
      { error: 'Revalidation failed' },
      { status: 500 }
    )
  }
}