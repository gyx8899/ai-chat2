// Model Store - 基于原项目完整实现
import { create } from 'zustand'

export interface Model {
  id: string
  name: string
  provider: string
  icon?: string
  description?: string
}

export interface FetchConfig {
  temperature?: number
  maxTokens?: number
  topP?: number
  topK?: number
  repetitionPenalty?: number
  stop?: string[]
  stream?: boolean
}

interface ModelState {
  models: Model[]
  selectedModel: string
  current: Model | null
  fetchConfig: FetchConfig
  loading: boolean
}

interface ModelActions {
  setModels: (models: Model[]) => void
  setSelectedModel: (model: string) => void
  setCurrent: (model: Model | null) => void
  setFetchConfig: (config: FetchConfig) => void
  updateFetchConfig: (config: Partial<FetchConfig>) => void
  setLoading: (loading: boolean) => void
  switchModel: (model: Model) => void
  loadModels: () => Promise<void>
}

type ModelStore = ModelState & ModelActions

export const useModelStore = create<ModelStore>((set) => ({
  models: [],
  selectedModel: '',
  current: null,
  fetchConfig: { temperature: 0.7, maxTokens: 2048, stream: true },
  loading: false,
  setModels: (models) => set({ models }),
  setSelectedModel: (model) => set({ selectedModel: model }),
  setCurrent: (model) => set({ current: model }),
  setFetchConfig: (config) => set({ fetchConfig: config }),
  updateFetchConfig: (config) => set((state) => ({ 
    fetchConfig: { ...state.fetchConfig, ...config } 
  })),
  setLoading: (loading) => set({ loading }),
  switchModel: (model) => set({ current: model, selectedModel: model.id }),
  loadModels: async () => {
    set({ loading: true })
    const controller = new AbortController()
    const timer = setTimeout(() => controller.abort(), 5000)
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080'
      const res = await fetch(`${baseUrl}/api/v1/config/models`, { signal: controller.signal })
      clearTimeout(timer)
      if (!res.ok) throw new Error('Failed to load models')
      const data = await res.json()
      // 后端返回 { models: [...] }
      const models = data.models || []
      set({ models, current: models[0] || null, loading: false })
    } catch (err) {
      clearTimeout(timer)
      // 超时或网络错误：返回默认模型列表
      console.warn('[models] 加载模型列表失败，返回默认值', err instanceof Error ? err.message : err)
      const defaults = [{ id: 'mock', name: 'Mock 模型', provider: 'mock', description: '默认模型（开发调试用）' }]
      set({ models: defaults, current: defaults[0], loading: false })
    }
  },
}))