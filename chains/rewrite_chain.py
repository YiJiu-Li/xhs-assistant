"""文案改写 Chain — 将原始文案改写为小红书风格"""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from config import API_BASE_URL, API_KEY, DEFAULT_MODEL, DEFAULT_TEMPERATURE, DEFAULT_MAX_TOKENS
from templates.xhs_templates import XHS_TEMPLATES

_COMMON_RULES = """通用规范（必须严格遵守）：
1. 标题：吸引眼球，20字以内，用数字/反问/悬念，标题前加1-2个emoji
2. 正文：分段落，每段不超过5行，段落之间空一行
3. Emoji 使用规范：每个段落至少1个emoji，关键词前后点缀，全文总计10-20个emoji
4. 语言：口语化、接地气，多用感叹号，避免书面语
5. 字数：200-400字
6. 结尾：必须加 3-5 个「小红书互动句」如「你们有没有同款体验～」「评论告诉我！」
7. 话题标签：正文最后单独一行，输出 8-10 个话题标签，格式：#标签1 #标签2 …（包含2个大流量通用标签+垂直标签+长尾标签）
8. 输出格式：先输出【标题】，再输出【正文+话题标签】"""


def get_llm(model: str = DEFAULT_MODEL, temperature: float = DEFAULT_TEMPERATURE, streaming: bool = False):
    return ChatOpenAI(
        model=model,
        temperature=temperature,
        max_tokens=DEFAULT_MAX_TOKENS,
        openai_api_key=API_KEY,
        openai_api_base=API_BASE_URL,
        streaming=streaming,
        stream_usage=True,
    )


def build_rewrite_chain(style: str, model: str = DEFAULT_MODEL, temperature: float = DEFAULT_TEMPERATURE):
    """构建普通文案改写 Chain（无 RAG）"""
    template_info = XHS_TEMPLATES.get(style, XHS_TEMPLATES["种草推荐"])
    style_guide = template_info["style_guide"].strip()

    system_prompt = f"""你是一位专业的小红书内容创作者，精通{style}风格的文案写作。

风格要求：
{style_guide}

{_COMMON_RULES}"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "请将以下原始文案改写为小红书{style}风格：\n\n{content}"),
    ])
    return prompt | get_llm(model, temperature, streaming=True)


def build_rag_rewrite_chain(style: str, model: str = DEFAULT_MODEL, temperature: float = DEFAULT_TEMPERATURE):
    """构建带 RAG 参考的文案改写 Chain（支持流式）"""
    template_info = XHS_TEMPLATES.get(style, XHS_TEMPLATES["种草推荐"])
    style_guide = template_info["style_guide"].strip()

    system_prompt = f"""你是一位专业的小红书内容创作者，精通{style}风格的文案写作。

风格要求：
{style_guide}

以下是从知识库中搜索到的爆款文案参考案例，请仔细学习其标题写法、段落结构、emoji 使用和互动语气，并将这些技巧融入你的改写中：
{{rag_context}}

{_COMMON_RULES}"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "请将以下原始文案改写为小红书{style}风格：\n\n{content}"),
    ])
    return prompt | get_llm(model, temperature, streaming=True)


def build_hashtag_chain(model: str = DEFAULT_MODEL):
    """构建话题标签生成 Chain"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是小红书标签策略专家。根据提供的文案内容，生成最优话题标签组合。

要求：
1. 生成8-12个标签
2. 包含：大流量通用标签（2-3个）+ 垂直领域标签（3-4个）+ 精准长尾标签（3-5个）
3. 每个标签前加 # 号
4. 标签之间用空格分隔
5. 只输出标签，不要其他内容"""),
        ("human", "请为以下小红书文案生成话题标签：\n\n{content}"),
    ])
    return prompt | get_llm(model, temperature=0.5)


def rewrite_with_rag(content: str, style: str, rag_context: str,
                     model: str = DEFAULT_MODEL, temperature: float = DEFAULT_TEMPERATURE) -> str:
    """结合 RAG 知识库的文案改写（同步，非流式）"""
    chain = build_rag_rewrite_chain(style, model, temperature)
    result = chain.invoke({"rag_context": rag_context, "style": style, "content": content})
    return result.content
