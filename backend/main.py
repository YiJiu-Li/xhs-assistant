"""小红书文案助手 — FastAPI 主入口"""

import os
import sys

# ── 确保根目录在 sys.path 中，使 chains/rag/templates/utils/config 均可导入 ──
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import rewrite, conversation, batch, knowledge, config as cfg_router, auth as auth_router


app = FastAPI(
    title="小红书文案助手 API",
    version="1.0.0",
    description="LangChain + FastAPI 驱动的小红书文案生成服务",
)

# ── CORS：允许 Vite 开发服务器访问 ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 挂载路由 ──
app.include_router(auth_router.router,  prefix="/api/auth",         tags=["认证"])
app.include_router(rewrite.router,      prefix="/api/rewrite",      tags=["改写"])
app.include_router(conversation.router, prefix="/api/conversation",  tags=["对话"])
app.include_router(batch.router,        prefix="/api/batch",         tags=["批量处理"])
app.include_router(knowledge.router,    prefix="/api/knowledge",     tags=["知识库"])
app.include_router(cfg_router.router,   prefix="/api/config",        tags=["配置"])


@app.get("/api/ping", tags=["健康检查"])
async def ping():
    return {"status": "ok", "message": "小红书文案助手 API 运行正常"}
