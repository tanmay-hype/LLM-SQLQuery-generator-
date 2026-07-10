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

class Settings(BaseSettings):
    openai_api_key: str = ""
    gemini_api_key: str = ""
    database_url: str = "sqlite:///./app.db"
    model_name: str = "gpt-4.1"
    app_name: str = "LLM SQL Generator"
    debug: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
    )

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()