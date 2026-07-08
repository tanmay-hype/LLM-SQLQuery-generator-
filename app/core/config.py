from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

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