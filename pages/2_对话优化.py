"""页面 2：对话式优化"""

import streamlit as st
from config import DEFAULT_MODEL, DEFAULT_TEMPERATURE
from chains.conversation_chain import build_conversation_chain, convert_history

st.set_page_config(page_title="对话优化 — 小红书助手", page_icon="💬", layout="wide")

st.title("💬 对话式文案优化")
st.markdown("与 AI 多轮对话，持续打磨你的文案")

model = st.session_state.get("selected_model", DEFAULT_MODEL)

# ===== 初始化对话历史 =====
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ===== 侧边操作 =====
with st.sidebar:
    st.markdown("### 💬 对话控制")

    # 快速导入上一次改写结果
    if "last_rewrite" in st.session_state:
        if st.button("📥 导入上次改写结果", use_container_width=True):
            last = st.session_state["last_rewrite"]
            st.session_state.chat_history = []
            init_msg = f"我有一篇小红书文案需要优化，内容如下：\n\n{last}"
            st.session_state.chat_history.append({"role": "user", "content": init_msg})
            # 获取AI初始回应
            chain = build_conversation_chain(model=model)
            history_msgs = convert_history(st.session_state.chat_history[:-1])
            response = chain.invoke({"history": history_msgs, "input": init_msg})
            st.session_state.chat_history.append({"role": "assistant", "content": response})
            st.rerun()

    if st.button("🗑️ 清空对话", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()

    st.divider()
    st.markdown("**💡 优化建议**")
    suggestions = [
        "帮我让标题更吸引人",
        "语气改得更活泼一点",
        "精简为200字以内",
        "针对18-25岁女生改写",
        "加强种草感，让人更想买",
        "改成更有知识感的风格",
        "重新生成话题标签",
    ]
    for sug in suggestions:
        if st.button(sug, use_container_width=True, key=f"sug_{sug}"):
            st.session_state["pending_input"] = sug

# ===== 对话界面 =====
chat_container = st.container()

with chat_container:
    if not st.session_state.chat_history:
        st.info("👋 你好！请将需要优化的文案粘贴进来，或从侧边栏导入上次改写结果，我来帮你打磨～")

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# ===== 输入框 =====
pending = st.session_state.pop("pending_input", None)
user_input = st.chat_input("输入你的修改需求...", key="chat_input")

# 处理快捷建议按钮触发
if pending and not user_input:
    user_input = pending

if user_input:
    # 显示用户消息
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # 调用 AI
    with st.chat_message("assistant"):
        with st.spinner("思考中..."):
            try:
                chain = build_conversation_chain(model=model)
                history_msgs = convert_history(st.session_state.chat_history[:-1])
                response = chain.invoke({
                    "history": history_msgs,
                    "input": user_input,
                })
                st.markdown(response)
                st.session_state.chat_history.append({"role": "assistant", "content": response})
            except Exception as e:
                err_msg = f"❌ 请求失败：{e}"
                st.error(err_msg)
                st.session_state.chat_history.append({"role": "assistant", "content": err_msg})
