"""页面 1：文案改写"""

import streamlit as st
from config import DEFAULT_MODEL, DEFAULT_TEMPERATURE
from templates.xhs_templates import XHS_TEMPLATES
from chains.rewrite_chain import build_rewrite_chain, build_hashtag_chain, rewrite_with_rag
from utils.helpers import extract_title_and_body, format_hashtags

st.set_page_config(page_title="文案改写 — 小红书助手", page_icon="📝", layout="wide")

st.title("📝 文案改写")
st.markdown("输入原始文案，AI 自动改写为小红书风格，并生成话题标签")

# 获取全局配置
model = st.session_state.get("selected_model", DEFAULT_MODEL)
temperature = st.session_state.get("temperature", DEFAULT_TEMPERATURE)

# ===== 配置区 =====
col_cfg1, col_cfg2, col_cfg3 = st.columns([2, 2, 1])

with col_cfg1:
    style = st.selectbox(
        "选择内容风格",
        options=list(XHS_TEMPLATES.keys()),
        format_func=lambda s: f"{XHS_TEMPLATES[s]['icon']} {s} — {XHS_TEMPLATES[s]['desc']}",
    )

with col_cfg2:
    gen_tags = st.toggle("自动生成话题标签", value=True)
    use_rag = st.toggle("RAG 知识库增强（参考爆款案例）", value=False)

with col_cfg3:
    st.markdown(f"**当前模型**")
    st.caption(f"`{model}`")

# 风格说明
with st.expander(f"{XHS_TEMPLATES[style]['icon']} 查看「{style}」风格说明"):
    st.markdown(f"""
**语气：** {XHS_TEMPLATES[style]['tone']}

**结构：** {XHS_TEMPLATES[style]['structure']}
""")

st.divider()

# ===== 输入区 =====
col_in, col_out = st.columns(2)

with col_in:
    st.markdown("### 📄 原始文案")
    user_input = st.text_area(
        label="原始文案内容",
        placeholder="在这里粘贴你想要改写的原始文案...\n\n可以是产品描述、活动通知、商品介绍、个人经历等任意内容。",
        height=280,
        label_visibility="collapsed",
    )

    btn_generate = st.button("✨ 开始改写", type="primary", use_container_width=True)

with col_out:
    st.markdown("### 🎨 改写结果")
    result_placeholder = st.empty()

# ===== 生成逻辑 =====
if btn_generate:
    if not user_input.strip():
        st.warning("请先输入要改写的原始文案")
    else:
        with st.spinner("AI 正在创作中..."):
            try:
                if use_rag:
                    from rag.vectorstore import get_rag_context
                    rag_ctx = get_rag_context(user_input, style=style, top_k=2)
                    result_text = rewrite_with_rag(
                        content=user_input,
                        style=style,
                        rag_context=rag_ctx,
                        model=model,
                        temperature=temperature,
                    )
                else:
                    chain = build_rewrite_chain(style=style, model=model, temperature=temperature)
                    result_text = chain.invoke({"style": style, "content": user_input})

                # 提取标题和正文
                title, body = extract_title_and_body(result_text)

                # 存入 session
                st.session_state["last_rewrite"] = result_text
                st.session_state["last_title"] = title
                st.session_state["last_body"] = body

                # 生成标签
                hashtags_text = ""
                if gen_tags:
                    tag_chain = build_hashtag_chain(model=model)
                    raw_tags = tag_chain.invoke({"content": result_text})
                    hashtags_text = format_hashtags(raw_tags)
                    st.session_state["last_hashtags"] = hashtags_text

            except Exception as e:
                st.error(f"生成失败：{e}")
                st.stop()

# 展示结果
if "last_rewrite" in st.session_state:
    with col_out:
        title = st.session_state.get("last_title", "")
        body = st.session_state.get("last_body", st.session_state["last_rewrite"])
        hashtags = st.session_state.get("last_hashtags", "")

        if title:
            st.markdown(f"**📌 标题**")
            st.info(title)

        st.markdown("**📝 正文**")
        st.text_area(
            "正文内容",
            value=body,
            height=220,
            label_visibility="collapsed",
            key="result_body_display",
        )

        if hashtags:
            st.markdown("**🏷️ 话题标签**")
            st.code(hashtags, language=None)

        # 复制区
        full_copy = f"{title}\n\n{body}\n\n{hashtags}" if title else f"{body}\n\n{hashtags}"
        st.text_area(
            "一键复制（全文）",
            value=full_copy.strip(),
            height=100,
            help="选中全部内容复制",
        )
