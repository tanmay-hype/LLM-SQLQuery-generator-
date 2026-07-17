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

    # Compatibility with existing env key MODEL_NAME.
    model_name: str = "gpt-4.1"

    gemini_api_key: str = ""

    gemini_model: str = "gemini-2.5-pro"

    ollama_base_url: str = "http://localhost:11434"

    ollama_model: str = "qwen2.5-coder:14b"

    # --------------------------------------------------
    # Schema Retrieval
    # --------------------------------------------------

    schema_retriever_top_k: int = 5

    schema_retriever_min_score: int = 5

    # Backward-compatible aliases for existing env keys.
    schema_retrieval_top_k: int = 5

    schema_retrieval_min_score: int = 5

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

# Module-level aliases used by existing imports.
OPENAI_API_KEY = settings.openai_api_key
OPENAI_MODEL = settings.openai_model
GEMINI_API_KEY = settings.gemini_api_key
GEMINI_MODEL = settings.gemini_model
OLLAMA_BASE_URL = settings.ollama_base_url
OLLAMA_MODEL = settings.ollama_model