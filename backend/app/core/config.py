"""应用配置管理"""
from pathlib import Path
from pydantic_settings import BaseSettings

# 获取 backend 目录的绝对路径
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent

# .env 文件的绝对路径
ENV_FILE_PATH = BACKEND_DIR / ".env"


class Settings(BaseSettings):
    """全局配置，从环境变量或 .env 文件读取"""
    APP_NAME: str = "Library AI Assistant"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    DATABASE_URL: str = f"sqlite:///{BACKEND_DIR / 'app' / 'data' / 'library.db'}"
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    CHROMA_PERSIST_DIR: str = f"{BACKEND_DIR / 'app' / 'data' / 'chroma'}"
    EMBEDDING_MODEL_NAME: str = "BAAI/bge-small-zh-v1.5"
    EMBEDDING_DEVICE: str = "cpu"
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 80
    TOP_K: int = 3
    SIMILARITY_THRESHOLD: float = 0.5

    # LLM 配置 (OpenAI 兼容 API)
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    LLM_MODEL_NAME: str = "qwen-plus"
    LLM_TEMPERATURE: float = 0
    LLM_MAX_TOKENS: int = 1024

    class Config:
        env_file = str(ENV_FILE_PATH)
        env_file_encoding = "utf-8"


settings = Settings()

# 调试信息
print(f"[Config] 配置文件路径: {ENV_FILE_PATH}")
print(f"[Config] 配置文件存在: {ENV_FILE_PATH.exists()}")
print(f"[Config] LLM API Key: {'已配置' if settings.LLM_API_KEY else '未配置'}")
