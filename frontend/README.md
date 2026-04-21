# 小红书 AI 文案助手 — 前端

基于 React 19 + TypeScript + Vite + Tailwind CSS v4 构建的前端应用。

## 开发环境启动

```bash
cd frontend
npm install
npm run dev        # 开发服务器：http://localhost:5173
```

> 前端默认请求 `http://localhost:8000`，请确保后端已启动。

## 构建生产包

```bash
npm run build      # 输出到 dist/
npm run preview    # 本地预览生产包
```

## 目录结构

```
src/
├── pages/          # 四大功能页面（改写 / 对话 / 批量 / 知识库）
├── components/     # 公共组件（Layout、MarkdownMessage、ProtectedRoute 等）
├── contexts/       # 全局上下文（AuthContext、ApiConfigContext）
├── hooks/          # 自定义 Hook
└── types/          # TypeScript 类型定义
```

## 技术栈

| 库 | 用途 |
|---|---|
| React 19 | UI 框架 |
| TypeScript | 类型安全 |
| Vite | 构建工具 |
| Tailwind CSS v4 | 原子化样式 |
| TanStack Query | 服务端状态管理 |
| React Router v7 | 客户端路由 |
| Axios | HTTP 请求 |


```js
export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...

      // Remove tseslint.configs.recommended and replace with this
      tseslint.configs.recommendedTypeChecked,
      // Alternatively, use this for stricter rules
      tseslint.configs.strictTypeChecked,
      // Optionally, add this for stylistic rules
      tseslint.configs.stylisticTypeChecked,

      // Other configs...
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```

You can also install [eslint-plugin-react-x](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-x) and [eslint-plugin-react-dom](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-dom) for React-specific lint rules:

```js
// eslint.config.js
import reactX from 'eslint-plugin-react-x'
import reactDom from 'eslint-plugin-react-dom'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...
      // Enable lint rules for React
      reactX.configs['recommended-typescript'],
      // Enable lint rules for React DOM
      reactDom.configs.recommended,
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```
