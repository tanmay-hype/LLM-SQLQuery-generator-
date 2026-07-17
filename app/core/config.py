from functools import lru_cache

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    """
    Application configuration.
    """

    # --------------------------------------------------
    # Application
    # --------------------------------------------------

    app_name: str = "LLM SQL Generator"

    debug: bool = False

    # --------------------------------------------------
    # Database
    # --------------------------------------------------

    database_url: str = "sqlite:///./app.db"

    postgres_user: str = "postgres"

    postgres_password: str = "postgres"

    postgres_db: str = "llm_sql"

    # --------------------------------------------------
    # LLM Providers
    # --------------------------------------------------

    openai_api_key: str = ""

    openai_model: str = "gpt-4.1"

    gemini_api_key: str = ""

    gemini_model: str = "gemini-2.5-pro"

    ollama_base_url: str = "http://localhost:11434"

    ollama_model: str = "qwen2.5-coder:14b"

    # --------------------------------------------------
    # Schema Retrieval
    # --------------------------------------------------

    settings.schema_retriever_top_k: int = 5

    settings.schema_retriever_min_score: int = 5

    # --------------------------------------------------
    # Example Retrieval
    # --------------------------------------------------

    example_retriever_top_k: int = 3

    example_retriever_min_score: int = 3

    # --------------------------------------------------
    # Prompt Generation
    # --------------------------------------------------

    max_prompt_examples: int = 3

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()