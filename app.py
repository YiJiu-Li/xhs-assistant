"""小红书文案助手 — 主页"""

import streamlit as st
from config import API_KEY, API_BASE_URL, MODELS, DEFAULT_MODEL

st.set_page_config(
    page_title="小红书文案助手",
    page_icon="📕",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ===== 侧边栏：全局配置 =====
with st.sidebar:
    st.markdown("## ⚙️ 全局配置")

    # API Key 检查
    api_key_input = st.text_input(
        "API Key",
        value=API_KEY,
        type="password",
        help="填入你的 API Key，或在 .env 文件中配置",
    )
    if api_key_input:
        import os
        os.environ["OPENAI_API_KEY"] = api_key_input

    # 模型选择
    model_options = list(MODELS.keys())
    selected_model = st.selectbox(
        "选择模型",
        options=model_options,
        index=model_options.index(DEFAULT_MODEL) if DEFAULT_MODEL in model_options else 0,
        format_func=lambda m: f"{m}  —  {MODELS[m]}",
    )
    st.session_state["selected_model"] = selected_model

    # Temperature
    temperature = st.slider(
        "创意度（Temperature）",
        min_value=0.0,
        max_value=1.5,
        value=0.85,
        step=0.05,
        help="越高越有创意，越低越保守稳定",
    )
    st.session_state["temperature"] = temperature

    st.divider()
    st.markdown(
        "<small>API Base: `https://api.pptoken.org/v1`</small>",
        unsafe_allow_html=True,
    )

# ===== 主页内容 =====
st.title("📕 小红书文案智能助手")
st.markdown("基于 **LangChain** 驱动的小红书风格文案二次创作平台")

st.divider()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
### 📝 文案改写
输入原始文案，一键改写为小红书风格

支持 **5种内容风格**：
- 🌟 种草推荐
- 📖 使用教程
- 📔 生活日记
- ⚖️ 测评对比
- 💕 情感共鸣

**自动生成话题标签**，可结合 RAG 知识库参考爆款案例
""")

with col2:
    st.markdown("""
### 💬 对话优化
多轮对话式文案打磨

- 实时与 AI 沟通修改需求
- 迭代优化标题、语气、结构
- 针对不同受众调整表达
- 历史对话上下文保留
""")

with col3:
    st.markdown("""
### 📦 批量处理
一次性处理多条文案

- 支持文本框输入（换行分隔）
- 支持 CSV / TXT 文件上传
- 实时进度显示
- 结果支持 Excel 导出
""")

with col4:
    st.markdown("""
### 📚 知识库管理
管理爆款文案 RAG 知识库

- 查看已有爆款案例
- 添加自定义优质文案
- 相似案例搜索预览
- 知识库清理维护
""")

st.divider()

# 快速开始
st.markdown("## 🚀 快速开始")

if not API_KEY and not api_key_input:
    st.warning("⚠️ 请先在左侧侧边栏填入 **API Key**，或在项目根目录创建 `.env` 文件配置（参考 `.env.example`）")
else:
    st.success("✅ API Key 已配置，请在左侧导航栏选择功能页面开始使用")

with st.expander("📋 使用说明 & 配置说明"):
    st.markdown("""
**1. 环境配置**
```bash
# 安装依赖
pip install -r requirements.txt

# 配置 API Key
cp .env.example .env
# 编辑 .env 填入你的 API Key
```

**2. 启动应用**
```bash
streamlit run app.py
```

**3. 首次使用 RAG 知识库**
- 进入「知识库管理」页面
- 点击「初始化知识库」加载内置爆款案例
- 之后在「文案改写」中开启 RAG 增强即可

**4. 模型选择建议**
| 场景 | 推荐模型 |
|------|---------|
| 日常改写 | gpt-5.4 |
| 批量处理 | gpt-5.2-codex |
| 快速预览 | gpt-5.1-codex-mini |
""")
