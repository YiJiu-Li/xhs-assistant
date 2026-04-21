"""对话历史存储 — 基于 LangChain SQLChatMessageHistory"""

import os
import sqlite3
from datetime import datetime
from langchain_community.chat_message_histories import SQLChatMessageHistory

# data/ 目录在项目根目录
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_DATA_DIR = os.path.join(_ROOT, "data")
_DB_PATH = os.path.join(_DATA_DIR, "chat_history.db")
# 使用同步 sqlite（aiosqlite 在同步初始化时会失败）
_CONNECTION_STRING = f"sqlite:///{_DB_PATH}"

# 确保 data/ 目录存在
os.makedirs(_DATA_DIR, exist_ok=True)


def _ensure_sessions_table():
    """确保 sessions 元数据表存在（含 user_id 列）"""
    conn = sqlite3.connect(_DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            user_id    TEXT NOT NULL DEFAULT ''
        )
    """)
    # 兼容旧表：若 user_id 列不存在则添加
    try:
        conn.execute("ALTER TABLE sessions ADD COLUMN user_id TEXT NOT NULL DEFAULT ''")
    except sqlite3.OperationalError:
        pass  # 列已存在
    conn.commit()
    conn.close()


def create_session_record(session_id: str, user_id: str = ""):
    """记录 session 创建时间和所属用户"""
    _ensure_sessions_table()
    conn = sqlite3.connect(_DB_PATH)
    conn.execute(
        "INSERT OR IGNORE INTO sessions (session_id, created_at, user_id) VALUES (?, ?, ?)",
        (session_id, datetime.now().strftime("%Y-%m-%d %H:%M"), user_id)
    )
    conn.commit()
    conn.close()


def get_session_history(session_id: str) -> SQLChatMessageHistory:
    """获取指定 session 的对话历史（自动创建表）"""
    return SQLChatMessageHistory(
        session_id=session_id,
        connection_string=_CONNECTION_STRING,
    )
