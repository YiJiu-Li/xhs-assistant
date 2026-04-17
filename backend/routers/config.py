"""配置接口 — 返回可用模型和风格模板列表"""

from fastapi import APIRouter
from config import MODELS, DEFAULT_MODEL
from templates.xhs_templates import XHS_TEMPLATES

router = APIRouter()


@router.get("/models")
async def get_models():
    return {
        "models": [
            {"id": k, "description": v, "default": k == DEFAULT_MODEL}
            for k, v in MODELS.items()
        ]
    }


@router.get("/templates")
async def get_templates():
    return {
        "templates": [
            {
                "id": k,
                "icon": v["icon"],
                "desc": v["desc"],
                "tone": v["tone"],
                "structure": v["structure"],
            }
            for k, v in XHS_TEMPLATES.items()
        ]
    }
