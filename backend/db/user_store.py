"""用户存储 — SQLite，密码 bcrypt 哈希"""

import os
import sqlite3
from datetime import datetime
from typing import Optional
import bcrypt

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_DB_PATH = os.path.join(_ROOT, "data", "users.db")

os.makedirs(os.path.dirname(_DB_PATH), exist_ok=True)

def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_table():
    conn = _get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT UNIQUE NOT NULL,
            hashed_pw   TEXT NOT NULL,
            created_at  TEXT NOT NULL,
            token_used  INTEGER NOT NULL DEFAULT 0,
            token_limit INTEGER NOT NULL DEFAULT 100000
        )
    """)
    conn.commit()
    # 兼容旧表：补充缺失字段
    for col, definition in [
        ("token_used",  "INTEGER NOT NULL DEFAULT 0"),
        ("token_limit", "INTEGER NOT NULL DEFAULT 100000"),
    ]:
        try:
            conn.execute(f"ALTER TABLE users ADD COLUMN {col} {definition}")
            conn.commit()
        except sqlite3.OperationalError:
            pass
    conn.close()


_ensure_table()


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_user(username: str, password: str) -> bool:
    """注册新用户，用户名重复返回 False"""
    try:
        conn = _get_conn()
        conn.execute(
            "INSERT INTO users (username, hashed_pw, created_at) VALUES (?, ?, ?)",
            (username.strip(), hash_password(password), datetime.now().isoformat()),
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False


def get_user(username: str) -> Optional[dict]:
    """按用户名查找用户，不存在返回 None"""
    conn = _get_conn()
    row = conn.execute(
        "SELECT id, username, hashed_pw FROM users WHERE username = ?",
        (username.strip(),),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def authenticate(username: str, password: str) -> Optional[dict]:
    """验证用户名密码，成功返回用户信息，失败返回 None"""
    user = get_user(username)
    if not user:
        return None
    if not verify_password(password, user["hashed_pw"]):
        return None
    return {"id": user["id"], "username": user["username"]}


def get_user_by_id(user_id: int) -> Optional[dict]:
    """按 ID 查找用户"""
    conn = _get_conn()
    row = conn.execute(
        "SELECT id, username, token_used, token_limit FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_quota(user_id: int) -> dict:
    """返回用户配额 {used, limit}"""
    conn = _get_conn()
    row = conn.execute(
        "SELECT token_used, token_limit FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    conn.close()
    return {"used": row[0], "limit": row[1]} if row else {"used": 0, "limit": 100000}


def add_token_usage(user_id: int, tokens: int) -> None:
    """累加用户 token 使用量"""
    if tokens <= 0:
        return
    conn = _get_conn()
    conn.execute(
        "UPDATE users SET token_used = token_used + ? WHERE id = ?",
        (tokens, user_id),
    )
    conn.commit()
    conn.close()


def has_quota(user_id: int) -> bool:
    """返回用户是否还有剩余配额"""
    q = get_user_quota(user_id)
    return q["used"] < q["limit"]


def set_token_limit(user_id: int, limit: int) -> None:
    """设置用户 token 上限（管理员用）"""
    conn = _get_conn()
    conn.execute("UPDATE users SET token_limit = ? WHERE id = ?", (limit, user_id))
    conn.commit()
    conn.close()
