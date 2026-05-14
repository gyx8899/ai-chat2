// UI Store - 基于原项目完整实现
import { create } from 'zustand'

export interface UIState {
  // 侧边栏
  sidebarOpen: boolean
  // 主题
  theme: 'light' | 'dark'
  // 是否是暗色模式
  isDark: boolean
  // 语言
  lang: 'zh-CN' | 'en'
  // 背景装饰
  bgDecor: boolean
  // 设置面板
  showSettings: boolean
  // 模型选择器
  showModelSelector: boolean
  // 调整面板
  showTweaksPanel: boolean
  tweaksOpen: boolean
  tweaksHue: number
  // 图片预览
  showImagePreview: boolean
  previewImageUrl: string
  // 滚动到底部
  showScrollToBottom: boolean
  // 用户菜单
  showUserMenu: boolean
}

interface UIActions {
  setSidebarOpen: (open: boolean) => void
  toggleSidebar: () => void
  setTheme: (theme: 'light' | 'dark') => void
  toggleDark: () => void
  setLang: (lang: 'zh-CN' | 'en') => void
  toggleLang: () => void
  setBgDecor: (show: boolean) => void
  toggleBgDecor: () => void
  setShowSettings: (show: boolean) => void
  setShowModelSelector: (show: boolean) => void
  setShowTweaksPanel: (show: boolean) => void
  setTweaksOpen: (open: boolean) => void
  setHue: (hue: number) => void
  setShowImagePreview: (show: boolean, url?: string) => void
  setShowScrollToBottom: (show: boolean) => void
  setShowUserMenu: (show: boolean) => void
}

type UIStore = UIState & UIActions

export const useUIStore = create<UIStore>((set) => ({
  // 初始状态
  sidebarOpen: false,
  theme: 'light',
  isDark: false,
  lang: 'zh-CN',
  bgDecor: true,
  showSettings: false,
  showModelSelector: false,
  showTweaksPanel: false,
  tweaksOpen: false,
  tweaksHue: 200,
  showImagePreview: false,
  previewImageUrl: '',
  showScrollToBottom: false,
  showUserMenu: false,
  // Actions
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setTheme: (theme) => set({ theme, isDark: theme === 'dark' }),
  toggleDark: () => set((state) => {
    const newTheme = state.isDark ? 'light' : 'dark'
    return { isDark: !state.isDark, theme: newTheme }
  }),
  setLang: (lang) => set({ lang }),
  toggleLang: () => set((state) => ({ lang: state.lang === 'zh-CN' ? 'en' : 'zh-CN' })),
  setBgDecor: (show) => set({ bgDecor: show }),
  toggleBgDecor: () => set((state) => ({ bgDecor: !state.bgDecor })),
  setShowSettings: (show) => set({ showSettings: show }),
  setShowModelSelector: (show) => set({ showModelSelector: show }),
  setShowTweaksPanel: (show) => set({ showTweaksPanel: show }),
  setTweaksOpen: (open) => set({ tweaksOpen: open }),
  setHue: (hue) => set({ tweaksHue: hue }),
  setShowImagePreview: (show, url = '') => set({ showImagePreview: show, previewImageUrl: url }),
  setShowScrollToBottom: (show) => set({ showScrollToBottom: show }),
  setShowUserMenu: (show) => set({ showUserMenu: show }),
}))