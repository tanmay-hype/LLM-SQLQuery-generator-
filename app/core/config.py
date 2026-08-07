from functools import lru_cache

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    """
    Application configuration.
    """

    # ==================================================
    # Application
    # ==================================================

    app_name: str = "LLM SQL Generator"
    debug: bool = False

    # ==================================================
    # Database
    # ==================================================

    database_url: str = "sqlite:///./app.db"

    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    postgres_db: str = "llm_sql"

    # ==================================================
    # OpenAI
    # ==================================================

    openai_api_key: str = ""
    openai_model: str = "gpt-4.1"

    # Backward compatibility
    model_name: str = "gpt-4.1"

    # ==================================================
    # Gemini
    # ==================================================

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-pro"

    gemini_embedding_model: str = "text-embedding-004"

    # ==================================================
    # Ollama
    # ==================================================

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5-coder:14b"

    # ==================================================
    # Schema Retrieval
    # ==================================================

    schema_retriever_top_k: int = 5
    schema_retriever_min_score: int = 5

    # Backward-compatible aliases
    schema_retrieval_top_k: int = 5
    schema_retrieval_min_score: int = 5

    schema_retrieval_strategy: str = "keyword"

    # ==================================================
    # Example Retrieval
    # ==================================================

    example_retriever_top_k: int = 3
    example_retriever_min_score: int = 3

    # ==================================================
    # Prompt Generation
    # ==================================================

    max_prompt_examples: int = 3
    
    # --------------------------------------------------
    # Vector Index
    # --------------------------------------------------

    faiss_index_path: str = "./storage/schema.index"

    schema_metadata_path: str = "./storage/schema_metadata.json"

    # ==================================================
    # SQL Correction
    # ==================================================

    sql_correction_max_attempts: int = 1

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()


# -------------------------------------------------------------------
# Backward-compatible aliases (optional)
# These allow older modules to continue working while you refactor.
# -------------------------------------------------------------------

OPENAI_API_KEY = settings.openai_api_key
OPENAI_MODEL = settings.openai_model

GEMINI_API_KEY = settings.gemini_api_key
GEMINI_MODEL = settings.gemini_model
GEMINI_EMBEDDING_MODEL = settings.gemini_embedding_model

OLLAMA_BASE_URL = settings.ollama_base_url
OLLAMA_MODEL = settings.ollama_model

SCHEMA_RETRIEVAL_STRATEGY = settings.schema_retrieval_strategy

SQL_CORRECTION_MAX_ATTEMPTS = settings.sql_correction_max_attempts