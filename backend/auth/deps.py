"""FastAPI 依赖 — 从 Authorization header 提取当前用户"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from backend.auth.jwt_utils import decode_token

_bearer = HTTPBearer(auto_error=False)


def _parse_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer)) -> Optional[dict]:
    """解析 token，返回 {sub, username} 或 None（不强制登录）"""
    if not credentials:
        return None
    payload = decode_token(credentials.credentials)
    if not payload:
        return None
    return {"user_id": payload["sub"], "username": payload.get("username", "")}


def get_current_user_optional(user=Depends(_parse_user)) -> Optional[dict]:
    """可选登录依赖（游客返回 None）"""
    return user


def get_current_user(user=Depends(_parse_user)) -> dict:
    """必须登录依赖，未登录抛 401"""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="请先登录",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
