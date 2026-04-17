"""页面 4：知识库管理"""

import streamlit as st
from templates.xhs_templates import XHS_TEMPLATES

st.set_page_config(page_title="知识库管理 — 小红书助手", page_icon="📚", layout="wide")

st.title("📚 爆款文案知识库")
st.markdown("管理 RAG 知识库，存储优质爆款文案案例，提升改写质量")


def load_vs():
    from rag.vectorstore import get_vectorstore
    return get_vectorstore()


# ===== Tab 布局 =====
tab_overview, tab_add, tab_search, tab_manage = st.tabs(
    ["📊 概览", "➕ 添加案例", "🔍 搜索预览", "🛠️ 管理维护"]
)

# ===== 概览 Tab =====
with tab_overview:
    st.markdown("### 知识库状态")

    col_init, col_stat = st.columns([1, 2])

    with col_init:
        if st.button("🔄 初始化知识库（加载内置样本）", type="primary", use_container_width=True):
            with st.spinner("正在初始化..."):
                try:
                    from rag.vectorstore import init_vectorstore_with_samples
                    init_vectorstore_with_samples()
                    st.success("✅ 知识库初始化完成，已加载 5 条内置爆款案例")
                    st.rerun()
                except Exception as e:
                    st.error(f"初始化失败：{e}")

    with col_stat:
        try:
            from rag.vectorstore import list_all_documents
            all_docs = list_all_documents()
            st.metric("知识库文案总数", len(all_docs))

            if all_docs:
                style_counts = {}
                for d in all_docs:
                    s = d["style"]
                    style_counts[s] = style_counts.get(s, 0) + 1
                st.markdown("**按风格分布：**")
                for s, cnt in style_counts.items():
                    icon = XHS_TEMPLATES.get(s, {}).get("icon", "📄")
                    st.write(f"{icon} {s}：{cnt} 条")
        except Exception as e:
            st.warning(f"无法读取知识库状态：{e}")

    st.divider()

    # 展示所有文档
    try:
        from rag.vectorstore import list_all_documents
        all_docs = list_all_documents()
        if all_docs:
            st.markdown(f"### 已存储文案（{len(all_docs)} 条）")
            for doc in all_docs:
                icon = XHS_TEMPLATES.get(doc["style"], {}).get("icon", "📄")
                with st.expander(f"{icon} {doc['title']} — {doc['style']} [{doc['source']}]"):
                    st.markdown(f"**预览：** {doc['content_preview']}")
                    if doc["hashtags"]:
                        st.code(doc["hashtags"], language=None)
                    st.caption(f"ID: `{doc['id']}`")
        else:
            st.info("知识库为空，请点击「初始化知识库」或手动添加案例")
    except Exception as e:
        st.error(f"读取失败：{e}")

# ===== 添加案例 Tab =====
with tab_add:
    st.markdown("### ➕ 添加爆款文案案例")

    add_style = st.selectbox(
        "文案风格",
        options=list(XHS_TEMPLATES.keys()),
        format_func=lambda s: f"{XHS_TEMPLATES[s]['icon']} {s}",
        key="add_style",
    )
    add_title = st.text_input("文案标题", placeholder="输入这篇文案的标题...")
    add_content = st.text_area("文案正文", placeholder="粘贴爆款文案正文内容...", height=200)
    add_hashtags = st.text_input("话题标签（可选）", placeholder="#标签1 #标签2 #标签3")
    add_source = st.text_input("来源备注", value="手动添加", placeholder="例如：小红书 / 自创")

    if st.button("✅ 添加到知识库", type="primary"):
        if not add_title.strip() or not add_content.strip():
            st.warning("标题和正文不能为空")
        else:
            try:
                from rag.vectorstore import add_document
                add_document(
                    title=add_title.strip(),
                    content=add_content.strip(),
                    style=add_style,
                    hashtags=add_hashtags.strip(),
                    source=add_source.strip(),
                )
                st.success(f"✅ 已成功添加：《{add_title}》")
            except Exception as e:
                st.error(f"添加失败：{e}")

# ===== 搜索预览 Tab =====
with tab_search:
    st.markdown("### 🔍 相似案例搜索")
    st.caption("输入文案内容，预览 RAG 会检索到哪些参考案例")

    search_query = st.text_area(
        "搜索内容",
        placeholder="粘贴你的文案或关键词...",
        height=120,
    )
    search_style = st.selectbox(
        "按风格筛选（可选）",
        options=["不限"] + list(XHS_TEMPLATES.keys()),
        key="search_style",
    )
    top_k = st.slider("返回数量", 1, 5, 3)

    if st.button("🔍 搜索相似案例"):
        if not search_query.strip():
            st.warning("请输入搜索内容")
        else:
            try:
                from rag.vectorstore import search_similar
                style_filter = None if search_style == "不限" else search_style
                results = search_similar(search_query, style=style_filter, top_k=top_k)
                if results:
                    st.markdown(f"找到 {len(results)} 条相似案例：")
                    for i, doc in enumerate(results, 1):
                        with st.expander(f"案例 {i}：{doc.metadata.get('title', '未知')}"):
                            st.markdown(doc.page_content)
                            st.caption(
                                f"风格：{doc.metadata.get('style', '未知')} | 来源：{doc.metadata.get('source', '未知')}"
                            )
                else:
                    st.info("未找到相似案例，请先初始化知识库")
            except Exception as e:
                st.error(f"搜索失败：{e}")

# ===== 管理维护 Tab =====
with tab_manage:
    st.markdown("### 🛠️ 知识库维护")

    st.warning("⚠️ 以下操作不可撤销，请谨慎操作")

    col_del, col_clear = st.columns(2)

    with col_del:
        st.markdown("**删除指定文档**")
        del_id = st.text_input("输入文档 ID", placeholder="从「概览」页复制文档 ID")
        if st.button("🗑️ 删除此文档"):
            if not del_id.strip():
                st.warning("请输入文档 ID")
            else:
                try:
                    from rag.vectorstore import delete_document
                    delete_document(del_id.strip())
                    st.success(f"✅ 已删除文档 `{del_id}`")
                    st.rerun()
                except Exception as e:
                    st.error(f"删除失败：{e}")

    with col_clear:
        st.markdown("**清空整个知识库**")
        st.caption("将删除所有文案记录（包括内置样本）")
        confirm = st.checkbox("我确认要清空知识库")
        if st.button("🧹 清空知识库", disabled=not confirm):
            try:
                from rag.vectorstore import clear_all_documents
                clear_all_documents()
                st.success("✅ 知识库已清空")
                st.rerun()
            except Exception as e:
                st.error(f"清空失败：{e}")
