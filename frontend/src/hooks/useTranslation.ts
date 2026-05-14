// useTranslation hook - 完整实现
// 基于 locales 模块提供翻译功能

import { useUIStore } from '@/store/uiStore'
import { translate, translateWithVars, type Locale, type TranslationKey } from '@/locales'

// 映射 UIStore 的 lang ('zh-CN' | 'en') 到 locales 的 Locale ('zh' | 'en')
function mapLangToLocale(lang: 'zh-CN' | 'en'): Locale {
  return lang === 'zh-CN' ? 'zh' : lang
}

export function useTranslation() {
  const lang = useUIStore((s) => s.lang)

  // 基础翻译函数
  const t = (key: TranslationKey): string => {
    return translate(mapLangToLocale(lang), key)
  }

  // 带变量的翻译函数
  const tv = (key: TranslationKey, vars?: Record<string, string | number>): string => {
    if (!vars) return translate(mapLangToLocale(lang), key)
    return translateWithVars(mapLangToLocale(lang), key, vars)
  }

  return {
    t,
    tv,
    locale: lang,
  }
}