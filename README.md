# 🌸 XHS Copilot · 小红书 AI 文案创作助手

> 基于 FastAPI + React + LangChain 的 AI 写作平台，集文案改写、对话优化、批量处理、RAG 知识库于一体，帮你轻松打造爆款小红书内容。

![预览](https://img.shields.io/badge/版本-1.0.0-ff2d55?style=flat-square) ![Python](https://img.shields.io/badge/Python-3.10+-3776ab?style=flat-square&logo=python&logoColor=white) ![React](https://img.shields.io/badge/React-19-61dafb?style=flat-square&logo=react&logoColor=white) ![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688?style=flat-square&logo=fastapi&logoColor=white)

---

## ✨ 功能特性

| 功能 | 描述 |
|------|------|
| 📝 **文案改写** | 支持多种小红书写作风格（种草、日记、测评等），SSE 流式输出 |
| 💬 **对话优化** | 多轮对话打磨文案，保存完整会话历史 |
| 📦 **批量处理** | 支持文本粘贴 / Excel 上传，批量生成改写结果并导出 |
| 📚 **知识库管理** | 基于 ChromaDB 的 RAG 向量知识库，支持添加、搜索、管理参考案例 |
| 🔐 **用户认证** | JWT 登录/注册，SQLite 用户库，Token 自动刷新 |
| 🪙 **Token 配额** | 每用户独立 Token 额度，实时统计消耗，超限自动拦截 |
| 🛡️ **内容守护** | 三层过滤（关键词白/黑名单 → LLM 快速分类 → 系统提示兜底），仅处理小红书相关内容 |

---

## 🛠 技术栈

**后端**
- [FastAPI](https://fastapi.tiangolo.com/) — 高性能异步 API 框架
- [LangChain](https://www.langchain.com/) — LLM 编排与 RAG 流水线
- [ChromaDB](https://www.trychroma.com/) — 本地向量数据库
- SQLite — 会话历史持久化
- SSE（Server-Sent Events）— 流式输出

**前端**
- [React 19](https://react.dev/) + [TypeScript](https://www.typescriptlang.org/)
- [Vite](https://vitejs.dev/) — 构建工具
- [Tailwind CSS v4](https://tailwindcss.com/) — 原子化样式
- [TanStack Query](https://tanstack.com/query) — 数据请求管理
- [React Router v7](https://reactrouter.com/) — 客户端路由

---

## 🚀 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- OpenAI API Key（或兼容的 API 服务）

### 1. 克隆项目

```bash
git clone https://github.com/YiJiu-Li/xhs-assistant.git
cd xhs-assistant
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`，填入你的 API Key：

```env
OPENAI_API_KEY=sk-xxxxxxxx
OPENAI_BASE_URL=https://api.openai.com/v1   # 可换成国内代理地址
OPENAI_MODEL=gpt-4o-mini
```

### 3. 安装后端依赖并启动

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt

python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

### 4. 启动前端

```bash
cd frontend
npm install
npm run dev
```

浏览器打开 http://localhost:5173 即可使用。

---

## 📁 项目结构

```
xhs-assistant/
├── backend/                # FastAPI 后端
│   ├── routers/            # 路由：改写 / 对话 / 批量 / 知识库 / 认证
│   ├── auth/               # JWT 签发与解析、Token 配额管理
│   ├── schemas/            # Pydantic 数据模型
│   └── db/                 # SQLite 用户库 & 会话存储
├── chains/                 # LangChain 链：改写 / 对话 / 批量
├── rag/                    # RAG 知识库（ChromaDB）
├── templates/              # 小红书风格提示词模板
├── content_scope.py        # 内容守护（三层过滤）
├── frontend/               # React 前端
│   └── src/
│       ├── pages/          # 四大功能页面
│       ├── components/     # 公共组件（Layout、MarkdownMessage）
│       └── contexts/       # 全局 API 配置上下文
├── .env.example            # 环境变量示例
└── requirements.txt        # Python 依赖
```

---

## 📸 界面预览

> 暖粉色系 UI，符合小红书品牌调性，PingFang SC 字体优先。

- 左侧导航栏：白底 + 品牌红高亮
- 主内容区：米白暖底 `#fff8f7`
- 主色调：`#ff2d55`（小红书品牌红）

---

## 🤝 贡献

欢迎提 Issue 或 PR！

---

## 📄 License

MIT
