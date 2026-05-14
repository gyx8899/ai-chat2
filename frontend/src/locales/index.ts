// 国际化模块 - 与原 ai/client 项目同步
// 基于原项目 src/locales/en.ts + src/locales/zh.ts 合并

export type Locale = 'zh' | 'en'
export type TranslationKey =
  | 'sidebar.title'
  | 'sidebar.subtitle'
  | 'sidebar.newChat'
  | 'sidebar.empty'
  | 'sidebar.untitled'
  | 'header.title'
  | 'header.subtitle'
  | 'header.toDark'
  | 'header.toLight'
  | 'header.switchLang'
  | 'header.openSidebar'
  | 'message.regenerate'
  | 'message.copy'
  | 'message.copied'
  | 'message.copyCode'
  | 'message.error'
  | 'message.ragPrefix'
  | 'message.thinking'
  | 'message.reasoning'
  | 'input.placeholder'
  | 'input.send'
  | 'input.stop'
  | 'input.disclaimer'
  | 'input.hintEnter'
  | 'input.hintShift'
  | 'input.hintNewline'
  | 'input.hintSend'
  | 'input.overLimit'
  | 'input.uploadImage'
  | 'input.removeImage'
  | 'input.imageTypeError'
  | 'input.imageSizeError'
  | 'input.imageMaxError'
  | 'empty.eyebrow'
  | 'empty.title'
  | 'empty.desc'
  | 'empty.s0Title'
  | 'empty.s0Desc'
  | 'empty.s1Title'
  | 'empty.s1Desc'
  | 'empty.s2Title'
  | 'empty.s2Desc'
  | 'empty.s3Title'
  | 'empty.s3Desc'
  | 'session.confirmDelete'
  | 'session.deleteConfirm'
  | 'session.deleteCancel'
  | 'sidebar.search'
  | 'sidebar.searchEmpty'
  | 'sidebar.groupToday'
  | 'sidebar.groupYesterday'
  | 'sidebar.groupEarlier'
  | 'sidebar.footerTitle'
  | 'sidebar.footerSubtitle'
  | 'sidebar.viewSource'
  | 'model.switch'
  | 'model.selectTitle'
  | 'model.loading'
  | 'message.offlineMode'
  | 'header.offlineMode'
  | 'message.onlineRestored'
  | 'message.errorDefault'
  | 'message.retry'
  | 'tweaks.title'
  | 'tweaks.brandHue'
  | 'tweaks.darkMode'
  | 'tweaks.bgDecor'
  | 'tweaks.collapse'
  | 'tweaks.open'
  | 'tweaks.toDark'
  | 'tweaks.toLight'
  | 'tweaks.hideBg'
  | 'tweaks.showBg'
  | 'localMode.reply'
  | 'fallback.title'
  | 'fallback.desc'
  | 'fallback.reload'

// 英文翻译资源
const en: Record<TranslationKey, string> = {
  // SidebarHeader
  'sidebar.title': 'AI Coding Assistant',
  'sidebar.subtitle': 'Frontend Expert',
  // Sidebar
  'sidebar.newChat': 'New Chat',
  'sidebar.empty': 'No conversations',
  'sidebar.untitled': 'New conversation',
  // ChatHeader
  'header.title': 'AI Coding Assistant',
  'header.subtitle': 'Frontend Expert · mock mode',
  'header.toDark': 'Switch to dark mode',
  'header.toLight': 'Switch to light mode',
  'header.switchLang': '切换为中文',
  'header.openSidebar': 'Open sidebar',
  // MessageList
  'message.regenerate': 'Regenerate',
  'message.copy': 'Copy',
  'message.copied': 'Copied',
  'message.copyCode': 'Copy code',
  'message.error': 'Sorry, an error occurred. Please try again.',
  'message.ragPrefix': 'Retrieved relevant knowledge: ',
  'message.thinking': 'Reasoning...',
  'message.reasoning': '💭 Reasoning',
  // InputArea
  'input.placeholder': 'Ask a coding question... Enter to send, Shift+Enter for newline',
  'input.send': 'Send',
  'input.stop': 'Stop',
  'input.disclaimer':
    'AI Coding Assistant provides programming-related answers for reference only.',
  'input.hintEnter': 'Enter',
  'input.hintShift': 'Shift',
  'input.hintNewline': 'newline',
  'input.hintSend': 'send',
  'input.overLimit': 'Input exceeds {max} character limit',
  'input.uploadImage': 'Upload image',
  'input.removeImage': 'Remove image',
  'input.imageTypeError': 'Only {types} formats are supported',
  'input.imageSizeError': 'Each image must not exceed {maxSize}MB',
  'input.imageMaxError': 'Maximum {max} images allowed',
  // EmptyState
  'empty.eyebrow': 'POWERED BY AI',
  'empty.title': 'Hi, how can I help you today?',
  'empty.desc':
    'Specialized in frontend development — React, Vue, TypeScript, Webpack and more.\nAnswers cover both design thinking and code implementation.',
  'empty.s0Title': 'React Hooks',
  'empty.s0Desc': 'What are the common Hooks and how to use them?',
  'empty.s1Title': 'Architecture',
  'empty.s1Desc': 'How to configure Webpack for code splitting?',
  'empty.s2Title': 'TypeScript',
  'empty.s2Desc': 'How to use generics in practice?',
  'empty.s3Title': 'CSS Layout',
  'empty.s3Desc': 'Flexbox vs. Grid — what is the difference?',
  // Session
  'session.confirmDelete': 'Confirm delete?',
  'session.deleteConfirm': 'Confirm',
  'session.deleteCancel': 'Cancel',
  'sidebar.search': 'Search conversations...',
  'sidebar.searchEmpty': 'No matching conversations',
  'sidebar.groupToday': 'Today',
  'sidebar.groupYesterday': 'Yesterday',
  'sidebar.groupEarlier': 'Earlier',
  'sidebar.footerTitle': 'Local Account',
  'sidebar.footerSubtitle': 'Workspace · Local',
  'sidebar.viewSource': 'View Source',
  'model.switch': 'Switch model',
  'model.selectTitle': 'Select model',
  'model.loading': 'Loading...',
  // Local mode
  'message.offlineMode': 'Model unavailable, switched to local mode',
  'header.offlineMode': 'Local Mode (Model Unavailable)',
  'message.onlineRestored': 'Model restored, switched back to online mode',
  // Error bubble
  'message.errorDefault': 'Request failed, please retry',
  'message.retry': 'Retry',
  // Tweaks Panel
  'tweaks.title': 'Tweaks',
  'tweaks.brandHue': 'Brand Hue',
  'tweaks.darkMode': 'Dark Mode',
  'tweaks.bgDecor': 'Background Decor',
  'tweaks.collapse': 'Collapse',
  'tweaks.open': 'Open Tweaks',
  'tweaks.toDark': 'Switch to dark mode',
  'tweaks.toLight': 'Switch to light mode',
  'tweaks.hideBg': 'Hide background decoration',
  'tweaks.showBg': 'Show background decoration',
  // Local mode reply
  'localMode.reply': 'The model/network is currently unavailable, please try again later.',
  // Error fallback
  'fallback.title': 'Something went wrong',
  'fallback.desc': 'Please refresh the page and try again',
  'fallback.reload': 'Refresh',
}

// 中文翻译资源
const zh: Record<TranslationKey, string> = {
  // SidebarHeader
  'sidebar.title': 'AI 编程助手',
  'sidebar.subtitle': '前端开发专家',
  // Sidebar
  'sidebar.newChat': '新建对话',
  'sidebar.empty': '暂无会话',
  'sidebar.untitled': '新对话',
  // ChatHeader
  'header.title': 'AI 编程助手',
  'header.subtitle': '精通前端开发 · mock 模式',
  'header.toDark': '切换到暗色模式',
  'header.toLight': '切换到亮色模式',
  'header.switchLang': 'Switch to English',
  'header.openSidebar': '打开侧边栏',
  // MessageList
  'message.regenerate': '重新生成',
  'message.copy': '复制',
  'message.copied': '已复制',
  'message.copyCode': '复制代码',
  'message.error': '抱歉，发生了错误，请重试。',
  'message.ragPrefix': '已检索到相关知识：',
  'message.thinking': '推理中…',
  'message.reasoning': '💭 推理过程',
  // InputArea
  'input.placeholder': '有什么编程问题？按 Enter 发送，Shift+Enter 换行',
  'input.send': '发送',
  'input.stop': '停止',
  'input.disclaimer': 'AI 编程助手仅提供编程相关解答，内容仅供参考',
  'input.hintEnter': 'Enter',
  'input.hintShift': 'Shift',
  'input.hintNewline': '换行',
  'input.hintSend': '发送',
  'input.overLimit': '输入内容超出 {max} 字符上限',
  'input.uploadImage': '上传图片',
  'input.removeImage': '移除图片',
  'input.imageTypeError': '仅支持 {types} 格式',
  'input.imageSizeError': '单张图片不能超过 {maxSize}MB',
  'input.imageMaxError': '最多上传 {max} 张图片',
  // EmptyState
  'empty.eyebrow': 'POWERED BY AI',
  'empty.title': '你好，我能帮你做些什么？',
  'empty.desc':
    '专注于前端开发领域，精通 React、Vue、TypeScript、Webpack 等。\n回答问题时从「设计思路」和「代码实现」两个维度输出。',
  'empty.s0Title': 'React Hooks',
  'empty.s0Desc': '常用 Hooks 有哪些？怎么使用？',
  'empty.s1Title': '架构设计',
  'empty.s1Desc': '如何配置 Webpack 实现代码分割？',
  'empty.s2Title': 'TypeScript',
  'empty.s2Desc': '泛型在实战中怎么使用？',
  'empty.s3Title': 'CSS 布局',
  'empty.s3Desc': 'Flexbox 和 Grid 有什么区别？',
  // Session
  'session.confirmDelete': '确认删除？',
  'session.deleteConfirm': '确认',
  'session.deleteCancel': '取消',
  'sidebar.search': '搜索会话...',
  'sidebar.searchEmpty': '未找到匹配会话',
  'sidebar.groupToday': '今天',
  'sidebar.groupYesterday': '昨天',
  'sidebar.groupEarlier': '更早',
  'sidebar.footerTitle': '本地账户',
  'sidebar.footerSubtitle': 'Workspace · Local',
  'sidebar.viewSource': '查看源码',
  'model.switch': '切换模型',
  'model.selectTitle': '选择模型',
  'model.loading': '加载中...',
  // 本地模式
  'message.offlineMode': '模型当前不可用，已切换至本地模式',
  'header.offlineMode': '本地模式（模型不可用）',
  'message.onlineRestored': '模型已恢复，已切换回在线模式',
  // 错误气泡
  'message.errorDefault': '请求失败，请重试',
  'message.retry': '重试',
  // Tweaks Panel
  'tweaks.title': '快速调节',
  'tweaks.brandHue': '品牌色相',
  'tweaks.darkMode': '暗色模式',
  'tweaks.bgDecor': '背景装饰',
  'tweaks.collapse': '收 起',
  'tweaks.open': '打开调节面板',
  'tweaks.toDark': '切换到暗色模式',
  'tweaks.toLight': '切换到亮色模式',
  'tweaks.hideBg': '隐藏背景装饰',
  'tweaks.showBg': '显示背景装饰',
  // 本地模式回复
  'localMode.reply': '当前模型/网络不可用，请稍后再试。',
  // 错误兜底
  'fallback.title': '页面出现异常',
  'fallback.desc': '请刷新页面重试',
  'fallback.reload': '刷新页面',
}

const resources: Record<Locale, Record<TranslationKey, string>> = {
  zh,
  en,
}

// 翻译函数
export function translate(lang: Locale, key: TranslationKey): string {
  return resources[lang][key] ?? resources.zh[key] ?? key
}

// 带变量的翻译函数
export function translateWithVars(
  lang: Locale,
  key: TranslationKey,
  vars: Record<string, string | number>
): string {
  let text = resources[lang][key] ?? resources.zh[key] ?? key
  for (const [k, v] of Object.entries(vars)) {
    text = text.replaceAll(`{${k}}`, String(v))
  }
  return text
}

// 获取所有支持的 locale
export function getLocales(): Locale[] {
  return ['zh', 'en']
}

// 获取 locale 显示名称
export function getLocaleName(locale: Locale): string {
  const names: Record<Locale, string> = {
    en: 'English',
    zh: '中文',
  }
  return names[locale]
}

// 导出默认翻译内容供 hook 使用
export const i18n = {
  translate,
  translateWithVars,
  getLocales,
  getLocaleName,
  translations: resources,
}