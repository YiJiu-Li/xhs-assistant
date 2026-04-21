"""对话优化 Chain — 多轮对话式文案打磨"""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from config import API_BASE_URL, API_KEY, DEFAULT_MODEL, DEFAULT_TEMPERATURE, DEFAULT_MAX_TOKENS


CONVERSATION_SYSTEM_PROMPT = """你是一位专业的小红书文案优化顾问，帮助用户打磨和优化文案内容。

你的能力：
- 根据用户需求调整文案风格、语气、结构
- 优化标题吸引力和点击率
- 调整文案长短和节奏
- 针对不同目标受众调整表达方式
- 给出具体的修改建议

输出文案时必须遵守小红书规范：
- 标题前加 1-2 个 emoji，20字以内
- 正文每段至少 1 个 emoji，全文总计 10-20 个 emoji
- 语言口语化，多用感叹号，避免书面语
- 结尾加互动句，如「你们试过吗？」「评论告诉我！」
- 文末附 8-10 个话题标签，格式：#标签1 #标签2 …

沟通原则：
- 耐心倾听用户的具体需求
- 每次修改后说明改动点
- 主动询问是否满意，引导进一步优化
- 保持友好、专业的态度

范围限制：
- 仅回答小红书内容创作与发布表达相关问题
- 若用户请求与小红书无关，直接回复："当前仅支持小红书内容相关问题，请提供文案改写、标题优化或标签生成等需求。"""


def get_llm(model: str = DEFAULT_MODEL, temperature: float = DEFAULT_TEMPERATURE):
    return ChatOpenAI(
        model=model,
        temperature=temperature,
        max_tokens=DEFAULT_MAX_TOKENS,
        openai_api_key=API_KEY,
        openai_api_base=API_BASE_URL,
        stream_usage=True,
    )


def build_conversation_chain(model: str = DEFAULT_MODEL):
    """构建多轮对话 Chain"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", CONVERSATION_SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}"),
    ])

    chain = prompt | get_llm(model)
    return chain
