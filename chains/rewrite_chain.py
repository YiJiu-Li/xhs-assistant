"""文案改写 Chain — 将原始文案改写为小红书风格"""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from config import API_BASE_URL, API_KEY, DEFAULT_MODEL, DEFAULT_TEMPERATURE, DEFAULT_MAX_TOKENS
from templates.xhs_templates import XHS_TEMPLATES


def get_llm(model: str = DEFAULT_MODEL, temperature: float = DEFAULT_TEMPERATURE):
    return ChatOpenAI(
        model=model,
        temperature=temperature,
        max_tokens=DEFAULT_MAX_TOKENS,
        openai_api_key=API_KEY,
        openai_api_base=API_BASE_URL,
    )


def build_rewrite_chain(style: str, model: str = DEFAULT_MODEL, temperature: float = DEFAULT_TEMPERATURE):
    """构建文案改写 Chain"""
    template_info = XHS_TEMPLATES.get(style, XHS_TEMPLATES["种草推荐"])
    style_guide = template_info["style_guide"].strip()

    system_prompt = f"""你是一位专业的小红书内容创作者，精通{style}风格的文案写作。

风格要求：
{style_guide}

通用规范（必须严格遵守）：
1. 标题：吸引眼球，20字以内，用数字/反问/悬念，标题前加1-2个emoji
2. 正文：分段落，每段不超过5行，段落之间空一行
3. Emoji 使用规范：每个段落至少1个emoji，关键词前后点缀，全文总计10-20个emoji
4. 语言：口语化、接地气，多用感叹号，避免书面语
5. 字数：200-400字
6. 结尾：必须加 3-5 个「小红书互动句」如「你们有没有同款体验～」「评论告诉我！」
7. 话题标签：正文最后单独一行，输出 8-10 个话题标签，格式：#标签1 #标签2 …（包含2个大流量通用标签+垂直标签+长尾标签）
8. 输出格式：先输出【标题】，再输出【正文+话题标签】"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "请将以下原始文案改写为小红书{style}风格：\n\n{content}"),
    ])

    chain = prompt | get_llm(model, temperature) | StrOutputParser()
    return chain


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

    chain = prompt | get_llm(model, temperature=0.5) | StrOutputParser()
    return chain


def rewrite_with_rag(content: str, style: str, rag_context: str,
                     model: str = DEFAULT_MODEL, temperature: float = DEFAULT_TEMPERATURE) -> str:
    """结合 RAG 知识库的文案改写"""
    template_info = XHS_TEMPLATES.get(style, XHS_TEMPLATES["种草推荐"])
    style_guide = template_info["style_guide"].strip()

    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""你是一位专业的小红书内容创作者，精通{style}风格的文案写作。

风格要求：
{style_guide}

以下是一些爆款文案参考案例，请从中学习写作技巧和风格：
{{rag_context}}

通用规范（必须严格遵守）：
1. 标题：吸引眼球，20字以内，标题前加1-2个emoji
2. 正文：分段落，每段不超过5行，段落之间空一行
3. Emoji 使用规范：每个段落至少1个emoji，关键词前后点缀，全文总计10-20个emoji
4. 语言：口语化、接地气，多用感叹号，避免书面语
5. 字数：200-400字
6. 结尾：加3-5个互动句，如「你们有没有同款体验～」「评论告诉我！」
7. 话题标签：正文最后单独一行，输出8-10个话题标签，格式：#标签1 #标签2 …（包含2个大流量通用标签+垂直标签+长尾标签）
8. 输出格式：先输出【标题】，再输出【正文+话题标签】"""),
        ("human", "请将以下原始文案改写为小红书{style}风格：\n\n{content}"),
    ])

    llm = get_llm(model, temperature)
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"rag_context": rag_context, "style": style, "content": content})
