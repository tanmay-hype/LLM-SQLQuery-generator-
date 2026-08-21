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

    database_url: str = ""

    postgres_user: str = "postgres"

    postgres_password: str = "postgres"

    postgres_db: str = "llm_sql"

    # ==================================================
    # OpenAI
    # ==================================================

    openai_api_key: str = ""

    openai_model: str = "gpt-4.1"

    # ==================================================
    # Gemini
    # ==================================================

    gemini_api_key: str = ""

    gemini_model: str = "gemini-2.5-pro"

    gemini_embedding_model: str = "gemini-embedding-2"

    # ==================================================
    # Ollama
    # ==================================================

    ollama_base_url: str = "http://localhost:11434"

    ollama_model: str = "qwen2.5-coder:14b"

    # ==================================================
    # Schema Retrieval
    # ==================================================

    schema_retrieval_strategy: str = "hybrid"

    schema_retrieval_top_k: int = 3

    schema_retrieval_min_score: int = 5
    
    schema_semantic_min_score: float = 0.60

    # ==================================================
    # Example Retrieval
    # ==================================================

    example_retriever_top_k: int = 3

    example_retriever_min_score: int = 3

    # ==================================================
    # Prompt Generation
    # ==================================================

    max_prompt_examples: int = 3

    # ==================================================
    # Vector Index
    # ==================================================

    faiss_index_path: str = "./storage/schema.index"

    schema_metadata_path: str = "./storage/schema_metadata.json"

    # ==================================================
    # SQL Correction
    # ==================================================

    sql_correction_max_attempts: int = 1

    # ==================================================
    # Pydantic Settings
    # ==================================================

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """
    Return cached application settings.
    """
    return Settings()


settings = get_settings()


# ==================================================
# Backward-compatible module-level aliases
# ==================================================

OPENAI_API_KEY = settings.openai_api_key
OPENAI_MODEL = settings.openai_model

GEMINI_API_KEY = settings.gemini_api_key
GEMINI_MODEL = settings.gemini_model
GEMINI_EMBEDDING_MODEL = settings.gemini_embedding_model

OLLAMA_BASE_URL = settings.ollama_base_url
OLLAMA_MODEL = settings.ollama_model

SCHEMA_RETRIEVAL_STRATEGY = settings.schema_retrieval_strategy

SQL_CORRECTION_MAX_ATTEMPTS = settings.sql_correction_max_attempts

