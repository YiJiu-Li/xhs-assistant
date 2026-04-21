"""认证接口 — 注册 / 登录 / 当前用户信息"""

import asyncio
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from backend.db.user_store import create_user, authenticate, get_user_quota
from backend.auth.jwt_utils import create_access_token
from backend.auth.deps import get_current_user

router = APIRouter()


class AuthRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=30)
    password: str = Field(..., min_length=6, max_length=100)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str


@router.post("/register", response_model=TokenResponse)
async def register(req: AuthRequest):
    """注册新账号并返回 token"""
    ok = await asyncio.to_thread(create_user, req.username, req.password)
    if not ok:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="用户名已被注册")
    user = await asyncio.to_thread(authenticate, req.username, req.password)
    token = create_access_token(user["id"], user["username"])
    return TokenResponse(access_token=token, username=user["username"])


@router.post("/login", response_model=TokenResponse)
async def login(req: AuthRequest):
    """登录并返回 token"""
    user = await asyncio.to_thread(authenticate, req.username, req.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    token = create_access_token(user["id"], user["username"])
    return TokenResponse(access_token=token, username=user["username"])


@router.get("/me")
async def me(user=Depends(get_current_user)):
    """获取当前用户信息及 Token 配额"""
    quota = get_user_quota(int(user["user_id"]))
    return {
        "user_id": user["user_id"],
        "username": user["username"],
        "quota": quota,
    }
