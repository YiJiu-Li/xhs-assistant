"""工具函数"""

import re


def extract_title_and_body(text: str) -> tuple[str, str]:
    """从模型输出中提取标题和正文"""
    title = ""
    body = text.strip()

    # 匹配 【标题】xxx 或 **标题：**xxx 格式
    title_patterns = [
        r"【标题】\s*(.+?)(?:\n|$)",
        r"\*\*标题[：:]\*\*\s*(.+?)(?:\n|$)",
        r"^标题[：:]\s*(.+?)(?:\n|$)",
        r"^#+\s+(.+?)(?:\n|$)",
    ]
    for pattern in title_patterns:
        match = re.search(pattern, text, re.MULTILINE)
        if match:
            title = match.group(1).strip()
            break

    # 提取正文部分
    body_patterns = [
        r"【正文】\s*([\s\S]+)$",
        r"\*\*正文[：:]\*\*\s*([\s\S]+)$",
        r"^正文[：:]\s*([\s\S]+)$",
    ]
    for pattern in body_patterns:
        match = re.search(pattern, text, re.MULTILINE)
        if match:
            body = match.group(1).strip()
            break
    else:
        # 没有明确标记时，去除标题行作为正文
        if title:
            body = re.sub(r"【标题】.+?\n", "", text, count=1).strip()
            body = re.sub(r"\*\*标题[：:]\*\*.+?\n", "", body, count=1).strip()

    return title, body


def count_tokens_approx(text: str) -> int:
    """粗略估算 token 数（中文约1.5字符/token，英文约4字符/token）"""
    chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
    other_chars = len(text) - chinese_chars
    return int(chinese_chars / 1.5 + other_chars / 4)


def split_text_by_lines(text: str, separator: str = "\n") -> list[str]:
    """按分隔符拆分文本，过滤空行"""
    lines = text.split(separator)
    return [line.strip() for line in lines if line.strip()]


def format_hashtags(raw: str) -> str:
    """规范化标签格式：确保每个标签以 # 开头，空格分隔"""
    tags = re.findall(r"#[\w\u4e00-\u9fff\-_]+", raw)
    return " ".join(tags)
