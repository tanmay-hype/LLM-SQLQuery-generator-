from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv
import os

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:14b")

SCHEMA_RETRIEVER_TOP_K = int(os.getenv("SCHEMA_RETRIEVER_TOP_K", 5))
SCHEMA_RETRIEVER_MIN_SCORE = int(os.getenv("SCHEMA_RETRIEVER_MIN_SCORE", 5))
class Settings(BaseSettings):
    openai_api_key: str = ""
    gemini_api_key: str = ""
    database_url: str = "sqlite:///./app.db"
    model_name: str = "gpt-4.1"
    app_name: str = "LLM SQL Generator"
    debug: bool = False
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    postgres_db: str = "llm_sql"
    schema_retriever_top_k: int = 5
    schema_retriever_min_score: int = 5
    schema_retrieval_top_k: int = 5
    schema_retrieval_min_score: int = 5

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
    )

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()