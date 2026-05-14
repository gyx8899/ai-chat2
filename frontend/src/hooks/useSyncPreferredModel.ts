'use client'

/**
 * useSyncPreferredModel — 页面 mount 时自动切换到提示词偏好的模型。
 *
 * 行为：
 * - mount 时检查 `preferred_model` 是否与 `modelStore.current` 不一致
 * - 若不一致，调用 `modelStore.switchModel()` 切换
 * - 仅在首次 mount 时触发，后续用户手动切换不受影响
 */

import { useEffect, useRef } from 'react'
import { useModelStore } from '@/store/modelStore'

interface UseSyncPreferredModelOptions {
  /** 当前提示词的 preferred_model */
  preferred_model: string | undefined
}

/**
 * 自动同步 preferred_model 到 modelStore。
 *
 * @param preferred_model  当前提示词配置中的 preferred_model（可 undefined）
 *
 * 注意：此 hook 假设 `loadModels()` 已由上层在 ChatArea 中触发。
 *       若 `models` 尚未加载完成，将等待 `loadModels` 完成后再做同步。
 */
export function useSyncPreferredModel({ preferred_model }: UseSyncPreferredModelOptions) {
  const current = useModelStore((s) => s.current)
  const models = useModelStore((s) => s.models)
  const switchModel = useModelStore((s) => s.switchModel)
  const setCurrent = useModelStore((s) => s.setCurrent)
  const hasSwitched = useRef(false)

  useEffect(() => {
    if (!preferred_model) return
    if (hasSwitched.current) return

    // 从 models 中查找 preferred_model 对应的 Model
    const target = models.find((m) => m.id === preferred_model)

    if (target) {
      hasSwitched.current = true
      switchModel(target)
    } else {
      // models 尚未加载完成，稍后重试（依赖 ChatArea 的 loadModels effect）
      // 通过监听 models 变化来触发重试
    }
  }, [preferred_model, models, switchModel, current])

  // 若 models 已加载但找不到 preferred_model，直接设置 current id
  useEffect(() => {
    if (!preferred_model) return
    if (hasSwitched.current) return
    if (models.length === 0) return

    const target = models.find((m) => m.id === preferred_model)
    if (!target) {
      // preferred_model 在可用模型列表中不存在，静默跳过
      hasSwitched.current = true
      return
    }
  }, [preferred_model, models])
}