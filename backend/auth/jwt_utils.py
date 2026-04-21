"""JWT 工具 — 签发与解析 access token"""

import os
import warnings
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt

_DEFAULT_SECRET = "xhs-assistant-secret-key-change-in-production"
_SECRET_KEY = os.environ.get("JWT_SECRET", _DEFAULT_SECRET)
if _SECRET_KEY == _DEFAULT_SECRET:
    warnings.warn(
        "JWT_SECRET 使用了默认值，生产环境请通过环境变量设置安全密钥！",
        stacklevel=1,
    )
_ALGORITHM = "HS256"
_EXPIRE_DAYS = 30  # token 有效期 30 天


def create_access_token(user_id: int, username: str) -> str:
    payload = {
        "sub": str(user_id),
        "username": username,
        "exp": datetime.utcnow() + timedelta(days=_EXPIRE_DAYS),
    }
    return jwt.encode(payload, _SECRET_KEY, algorithm=_ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    """解析 token，失败返回 None"""
    try:
        return jwt.decode(token, _SECRET_KEY, algorithms=[_ALGORITHM])
    except JWTError:
        return None
