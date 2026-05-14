"""Knowledge 模块 - 预设知识库。

重构自 app/data/knowledge.py - 提供前端开发知识库。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class KnowledgeItem:
    """知识库条目。"""

    id: str
    keywords: list[str]
    content: str


# 预设知识库
KNOWLEDGE_BASE: list[KnowledgeItem] = [
    KnowledgeItem(
        id="react-hooks",
        keywords=[
            "react",
            "hooks",
            "useState",
            "useEffect",
            "useRef",
            "useMemo",
            "useCallback",
            "钩子",
            "组件",
        ],
        content="""## React Hooks 核心概念

**useState** - 状态管理
```jsx
const [count, setCount] = useState(0);
```

**useEffect** - 副作用处理
```jsx
useEffect(() => {
  // 组件挂载或依赖变化时执行
  return () => { /* 清理函数 */ };
}, [dependency]);
```

**useMemo / useCallback** - 性能优化，避免不必要的重计算和重渲染。

**规则**：只在函数组件顶层调用 Hook，不在循环、条件或嵌套函数中调用。""",
    ),
    KnowledgeItem(
        id="webpack-config",
        keywords=[
            "webpack",
            "打包",
            "bundle",
            "loader",
            "plugin",
            "构建",
            "配置",
            "vite",
            "工程化",
        ],
        content="""## Webpack 核心配置

```js
module.exports = {
  entry: './src/index.js',
  output: { path: path.resolve(__dirname, 'dist'), filename: '[name].[contenthash].js' },
  module: {
    rules: [
      { test: /\\.tsx?$/, use: 'ts-loader' },
      { test: /\\.css$/, use: ['style-loader', 'css-loader'] }
    ]
  },
  plugins: [new HtmlWebpackPlugin({ template: './public/index.html' })],
  optimization: { splitChunks: { chunks: 'all' } }
};
```

**关键概念**：Entry（入口）、Output（输出）、Loader（转换器）、Plugin（插件）、Code Splitting（代码分割）。""",
    ),
    KnowledgeItem(
        id="typescript-basics",
        keywords=[
            "typescript",
            "ts",
            "类型",
            "interface",
            "type",
            "泛型",
            "generic",
            "类型推断",
        ],
        content="""## TypeScript 核特性

**接口与类型别名**
```ts
interface User { id: number; name: string; email?: string; }
type Status = 'active' | 'inactive' | 'pending';
```

**泛型**
```ts
function identity<T>(arg: T): T { return arg; }
const result = identity<string>('hello');
```

**常用工具类型**：`Partial<T>`、`Required<T>`、`Pick<T, K>`、`Omit<T, K>`、`Record<K, V>`""",
    ),
    KnowledgeItem(
        id="css-layout",
        keywords=[
            "css",
            "flex",
            "grid",
            "布局",
            "flexbox",
            "响应式",
            "tailwind",
            "样式",
        ],
        content="""## CSS 现代布局

**Flexbox**
```css
.container {
  display: flex;
  justify-content: space-between; /* 主轴对齐 */
  align-items: center;            /* 交叉轴对齐 */
  gap: 16px;
}
```

**CSS Grid**
```css
.grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; }
```

**响应式**：使用 `@media (max-width: 768px)` 断点，或 Tailwind 的 `sm:`、`md:`、`lg:` 前缀。""",
    ),
    KnowledgeItem(
        id="vue-composition",
        keywords=[
            "vue",
            "vue3",
            "composition",
            "ref",
            "reactive",
            "computed",
            "组合式",
            "选项式",
        ],
        content="""## Vue 3 组合式 API

```vue
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';

const count = ref(0);
const doubled = computed(() => count.value * 2);

onMounted(() => console.log('组件已挂载'));
</script>
```

**ref vs reactive**：基本类型用 `ref`，对象用 `reactive`。访问 ref 需要 `.value`，在模板中自动解包。""",
    ),
    KnowledgeItem(
        id="performance",
        keywords=[
            "性能",
            "优化",
            "懒加载",
            "lazy",
            "虚拟列表",
            "缓存",
            "memo",
            "首屏",
            "lighthouse",
        ],
        content="""## 前端性能优化

**代码层面**
- React：`React.memo`、`useMemo`、`useCallback` 避免不必要渲染
- 路由懒加载：`const Page = React.lazy(() => import('./Page'))`
- 虚拟列表：大量数据使用 `react-virtual` 或 `vue-virtual-scroller`

**资源层面**
- 图片：WebP 格式、懒加载 `loading="lazy"`、CDN 加速
- JS：Tree Shaking、Code Splitting、Gzip/Brotli 压缩

**指标**：关注 LCP（最大内容绘制）< 2.5s、FID < 100ms、CLS < 0.1""",
    ),
]


@dataclass
class RAGResult:
    """RAG 检索结果。"""

    hint: str  # 命中的知识 ID 列表（逗号分隔）
    context: str  # 命中的知识内容（Markdown 格式）


def retrieve_context(query: str) -> Optional[RAGResult]:
    """根据用户查询从知识库中检索相关内容。

    通过关键词交集匹配，返回最相关的 1~2 条知识片段。

    Args:
        query: 用户输入

    Returns:
        RAGResult | None: 匹配结果，无匹配时返回 None
    """
    query_lower = query.lower()

    # 计算每条知识的匹配分数（关键词命中数量）
    scored = [
        {
            "id": item.id,
            "content": item.content,
            "score": sum(1 for kw in item.keywords if kw.lower() in query_lower),
        }
        for item in KNOWLEDGE_BASE
    ]

    # 过滤出有匹配的条目，按分数降序取前 2 条
    matched = sorted(
        [item for item in scored if item["score"] > 0],
        key=lambda x: x["score"],
        reverse=True,
    )[:2]

    if not matched:
        return None

    hint = ", ".join(item["id"] for item in matched)
    context = "\n\n---\n\n".join(item["content"] for item in matched)

    return RAGResult(hint=hint, context=context)


__all__ = ["KnowledgeItem", "RAGResult", "KNOWLEDGE_BASE", "retrieve_context"]