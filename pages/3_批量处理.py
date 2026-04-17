"""页面 3：批量处理"""

import io
import pandas as pd
import streamlit as st
from config import DEFAULT_MODEL, FAST_MODEL, BATCH_MAX_SIZE
from templates.xhs_templates import XHS_TEMPLATES
from chains.batch_chain import process_batch
from utils.helpers import split_text_by_lines

st.set_page_config(page_title="批量处理 — 小红书助手", page_icon="📦", layout="wide")

st.title("📦 批量文案处理")
st.markdown(f"一次处理最多 **{BATCH_MAX_SIZE}** 条文案，自动改写 + 生成标签")

model = st.session_state.get("selected_model", FAST_MODEL)

# ===== 配置 =====
col1, col2, col3 = st.columns(3)
with col1:
    style = st.selectbox(
        "统一应用风格",
        options=list(XHS_TEMPLATES.keys()),
        format_func=lambda s: f"{XHS_TEMPLATES[s]['icon']} {s}",
    )
with col2:
    gen_tags = st.toggle("生成话题标签", value=True)
with col3:
    use_fast_model = st.toggle("使用快速模型（节省时间）", value=True)
    batch_model = FAST_MODEL if use_fast_model else model

st.divider()

# ===== 输入区 =====
tab_text, tab_file = st.tabs(["✍️ 文本输入", "📁 文件上传"])

texts_to_process: list[str] = []

with tab_text:
    raw_text = st.text_area(
        "每行一条文案（换行分隔）",
        placeholder="第一条文案内容...\n第二条文案内容...\n第三条文案内容...",
        height=200,
    )
    if raw_text.strip():
        texts_to_process = split_text_by_lines(raw_text, separator="\n")
        st.caption(f"检测到 {len(texts_to_process)} 条文案")

with tab_file:
    uploaded_file = st.file_uploader(
        "上传 TXT 或 CSV 文件",
        type=["txt", "csv"],
        help="TXT：每行一条文案；CSV：需包含名为 content 或第一列为文案内容",
    )
    if uploaded_file:
        if uploaded_file.name.endswith(".txt"):
            content = uploaded_file.read().decode("utf-8")
            texts_to_process = split_text_by_lines(content, separator="\n")
        elif uploaded_file.name.endswith(".csv"):
            df_upload = pd.read_csv(uploaded_file)
            col_name = "content" if "content" in df_upload.columns else df_upload.columns[0]
            texts_to_process = df_upload[col_name].dropna().astype(str).tolist()
        st.caption(f"文件中检测到 {len(texts_to_process)} 条文案")
        if len(texts_to_process) > BATCH_MAX_SIZE:
            st.warning(f"超过上限，将只处理前 {BATCH_MAX_SIZE} 条")
            texts_to_process = texts_to_process[:BATCH_MAX_SIZE]

# ===== 处理按钮 =====
btn_batch = st.button(
    f"🚀 开始批量处理（{len(texts_to_process)} 条）",
    type="primary",
    disabled=len(texts_to_process) == 0,
    use_container_width=True,
)

# ===== 处理逻辑 =====
if btn_batch and texts_to_process:
    results = []
    progress_bar = st.progress(0, text="准备中...")
    status_text = st.empty()
    total = len(texts_to_process)

    for result in process_batch(texts_to_process, style=style, model=batch_model, generate_tags=gen_tags):
        results.append(result)
        pct = result["index"] / total
        progress_bar.progress(pct, text=f"处理中 {result['index']}/{total}...")
        status_icon = "✅" if result["status"] == "ok" else "❌"
        status_text.markdown(f"{status_icon} 第 {result['index']} 条：{result['original'][:30]}...")

    progress_bar.progress(1.0, text="处理完成！")
    status_text.empty()

    st.session_state["batch_results"] = results
    success_count = sum(1 for r in results if r["status"] == "ok")
    st.success(f"✅ 完成！成功 {success_count} 条，失败 {total - success_count} 条")

# ===== 展示结果 =====
if "batch_results" in st.session_state:
    results = st.session_state["batch_results"]
    st.divider()
    st.markdown(f"### 📋 处理结果（{len(results)} 条）")

    # 导出按钮
    df_export = pd.DataFrame([
        {
            "序号": r["index"],
            "原始文案": r["original"],
            "改写结果": r["rewritten"],
            "话题标签": r["hashtags"],
            "状态": r["status"],
            "错误信息": r["error"],
        }
        for r in results
    ])
    excel_buffer = io.BytesIO()
    df_export.to_excel(excel_buffer, index=False, engine="openpyxl")
    st.download_button(
        label="📥 下载 Excel 结果",
        data=excel_buffer.getvalue(),
        file_name="xhs_batch_results.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    # 逐条展示
    for r in results:
        status_icon = "✅" if r["status"] == "ok" else "❌"
        with st.expander(f"{status_icon} 第 {r['index']} 条：{r['original'][:40]}..."):
            col_l, col_r = st.columns(2)
            with col_l:
                st.markdown("**原始文案**")
                st.text(r["original"])
            with col_r:
                st.markdown("**改写结果**")
                if r["status"] == "ok":
                    st.text(r["rewritten"])
                    if r["hashtags"]:
                        st.code(r["hashtags"], language=None)
                else:
                    st.error(r["error"])
