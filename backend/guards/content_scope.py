"""小红书内容范围守卫 — 三层过滤架构

Layer 1: 关键词快速判定 (<1ms)
  - 白名单命中 → 直接放行
  - 黑名单命中（无白） → 直接拒绝
  - 灰区 → 进入 Layer 2（仅首轮对话触发）
Layer 2: LLM 意图二判（MINI 模型，~0.5s，仅灰区首轮触发）
  - 异常时默认放行，避免误杀
Layer 3: System prompt 兜底（在 chain 层完成）
"""
from __future__ import annotations

# ── Layer 1 白名单：命中即放行 ────────────────────────────────────────────────
XHS_INTENT_KEYWORDS: frozenset[str] = frozenset({
    "小红书", "笔记", "文案", "改写", "润色", "优化", "标题", "封面", "开头",
    "结尾", "互动句", "话题", "标签", "种草", "探店", "测评", "口播", "脚本",
    "爆款", "收藏", "点赞", "评论", "转化", "引流", "人设", "风格",
    "好物", "分享", "推荐", "安利", "晒", "日记", "体验", "开箱", "vlog",
    "打卡", "攻略", "合集", "清单", "教程", "心得", "评测",
    "美食", "护肤", "穿搭", "旅行", "健身", "美妆", "母婴", "宠物",
    "家居", "数码", "学习", "减肥", "装修", "植物", "汉服",
    "滑雪", "露营", "咖啡", "甜品", "下午茶", "素食",
    "写一篇", "写一段", "帮我写", "生成", "创作",
})

# ── Layer 1 黑名单：无白名单命中时直接拒绝 ────────────────────────────────────
STRONG_OFFTOPIC_KEYWORDS: frozenset[str] = frozenset({
    "python", "java", "javascript", "typescript", "c++", "go语言", "rust", "php",
    "sql语句", "代码", "编程", "算法", "数据结构", "正则表达式", "api接口",
    "微积分", "方程", "高数", "数学题", "物理题", "化学题", "作业答案",
    "法律咨询", "合同纠纷", "医疗诊断", "处方", "病情诊断",
    "炒股", "股票代码", "币圈", "基金净值", "期货",
    "面试题", "八字", "算命", "占卜", "黑客", "破解密码",
})

REJECTION_MESSAGE = (
    "当前助手仅支持小红书内容相关请求（如文案改写、标题优化、标签生成、发布表达优化）。"
    "请改为小红书场景后再试。"
)

_CLASSIFIER_SYSTEM = "你是意图分类器，只回答 yes 或 no，不要解释。"
_CLASSIFIER_HUMAN = (
    "判断以下输入是否属于\"小红书内容创作\"范围。\n\n"
    "属于（yes）：写作/改写/优化生活内容（美食、旅行、护肤、穿搭等）、"
    "生成标签/标题/文案、询问小红书写作技巧、提供原文请求改写。\n"
    "不属于（no）：编程代码、学科题目、天气/新闻查询、"
    "医疗/法律建议、金融投资、无关闲聊。\n\n"
    "输入：{text}"
)


def _normalize(text: str) -> str:
    return (text or "").strip().lower()


def has_xhs_intent(text: str) -> bool:
    n = _normalize(text)
    return any(kw in n for kw in XHS_INTENT_KEYWORDS)


def is_clearly_offtopic(text: str) -> bool:
    n = _normalize(text)
    if not n or has_xhs_intent(n):
        return False
    return any(kw in n for kw in STRONG_OFFTOPIC_KEYWORDS)


def is_strongly_offtopic(text: str) -> bool:
    return is_clearly_offtopic(text)


async def _llm_is_xhs_related(text: str) -> bool:
    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.prompts import ChatPromptTemplate
        from config import API_BASE_URL, API_KEY, MINI_MODEL
        llm = ChatOpenAI(
            model=MINI_MODEL,
            temperature=0,
            max_tokens=5,
            openai_api_key=API_KEY,
            openai_api_base=API_BASE_URL,
        )
        prompt = ChatPromptTemplate.from_messages([
            ("system", _CLASSIFIER_SYSTEM),
            ("human", _CLASSIFIER_HUMAN),
        ])
        chain = prompt | llm
        result = await chain.ainvoke({"text": text[:500]})
        return result.content.strip().lower().startswith("y")
    except Exception:
        return True


async def check_scope(text: str, has_history: bool = False) -> tuple[bool, str]:
    n = _normalize(text)
    if not n:
        return False, ""
    if has_history:
        if is_clearly_offtopic(n):
            return True, REJECTION_MESSAGE
        return False, ""
    if has_xhs_intent(n):
        return False, ""
    if is_clearly_offtopic(n):
        return True, REJECTION_MESSAGE
    related = await _llm_is_xhs_related(text)
    if not related:
        return True, REJECTION_MESSAGE
    return False, ""


def should_reject_conversation_message(text: str, has_history: bool) -> bool:
    n = _normalize(text)
    if not n:
        return False
    if not has_history:
        return not has_xhs_intent(n)
    return is_clearly_offtopic(n)
