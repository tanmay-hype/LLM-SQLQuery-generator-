from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv
import os

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1")

class Settings(BaseSettings):
    openai_api_key: str
    database_url: str
    model_name: str = "gpt-4.1"
    app_name: str
    debug: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,)

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()