import os
from dotenv import load_dotenv

load_dotenv()

# ===== API 配置 =====
API_BASE_URL = os.getenv("OPENAI_API_BASE", "https://api.pptoken.org/v1")
API_KEY = os.getenv("OPENAI_API_KEY", "")

# ===== 模型列表 =====
MODELS = {
    "gpt-5.4": "综合能力强，适合作为默认",
    "gpt-5.3-codex": "稳定、成本更低",
    "gpt-5.2-codex": "响应更快，适合高频任务",
    "gpt-5.3-codex-spark": "轻量问答与快任务",
    "gpt-5.1-codex-mini": "低成本短任务",
    "codex-mini-latest": "兜底可选",
}

DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-5.4")
FAST_MODEL = "gpt-5.2-codex"
MINI_MODEL = "gpt-5.1-codex-mini"

# ===== RAG 配置 =====
CHROMA_DB_PATH = "./data/chroma_db"
COLLECTION_NAME = "xhs_samples"

# ===== 生成参数 =====
DEFAULT_TEMPERATURE = 0.85
DEFAULT_MAX_TOKENS = 1500
BATCH_MAX_SIZE = 20
