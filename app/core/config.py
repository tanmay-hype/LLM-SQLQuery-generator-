from functools import lru_cache

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict


load_dotenv()


class Settings(BaseSettings):
    """
    Application configuration.

    Values are loaded from environment variables and/or
    the local .env file.

    Environment variable names are case-insensitive.

    Example:

        LLM_PROVIDER=gemini
        GEMINI_MODEL=gemini-2.5-pro
        SCHEMA_RETRIEVAL_TOP_K=3
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
    # LLM Provider
    # ==================================================

    # Explicitly selects the SQL-generation provider.
    #
    # Supported values:
    #
    #     gemini
    #     openai
    #     ollama
    #
    # For your current development setup:
    #
    #     LLM_PROVIDER=gemini
    #
    llm_provider: str = "gemini"

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

    # Maximum number of embeddings stored in the
    # process-local LRU embedding cache.
    
    embedding_cache_size: int = 256

    # ==================================================
    # Ollama
    # ==================================================

    # Docker Compose service name is "ollama", therefore
    # application containers should use:
    #
    #     http://ollama:11434
    #
    # rather than localhost.
    ollama_base_url: str = "http://ollama:11434"

    ollama_model: str = "qwen2.5-coder:14b"
    
    
    # ------------------------------------------------------
    # SQL CACHE
    # ------------------------------------------------------

    sql_cache_enabled: bool = True
    sql_cache_size: int = 256

    # ==================================================
    # Schema Retrieval
    # ==================================================

    schema_retrieval_strategy: str = "hybrid"

    # Maximum number of relevance seed tables selected
    # before relationship-aware bridge expansion.
    schema_retrieval_top_k: int = 3

    # Minimum deterministic keyword relevance score.
    schema_retrieval_min_score: int = 5

    # Absolute semantic similarity threshold.
    schema_semantic_min_score: float = 0.60

    # Maximum allowed score difference from the strongest
    # semantic retrieval match.
    schema_semantic_max_score_gap: float = 0.10

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
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


# ======================================================
# SETTINGS SINGLETON
# ======================================================

@lru_cache
def get_settings() -> Settings:
    """
    Return the cached application settings instance.

    The cache ensures the application does not repeatedly
    re-read and rebuild Settings throughout the process.
    """

    return Settings()


settings = get_settings()


# ======================================================
# BACKWARD-COMPATIBLE MODULE-LEVEL ALIASES
# ======================================================

# ------------------------------------------------------
# LLM Provider
# ------------------------------------------------------

LLM_PROVIDER = settings.llm_provider

# ------------------------------------------------------
# OpenAI
# ------------------------------------------------------

OPENAI_API_KEY = settings.openai_api_key

OPENAI_MODEL = settings.openai_model

# ------------------------------------------------------
# Gemini
# ------------------------------------------------------

GEMINI_API_KEY = settings.gemini_api_key

GEMINI_MODEL = settings.gemini_model

GEMINI_EMBEDDING_MODEL = (
    settings.gemini_embedding_model
)

# ------------------------------------------------------
# Ollama
# ------------------------------------------------------

OLLAMA_BASE_URL = settings.ollama_base_url

OLLAMA_MODEL = settings.ollama_model

# ------------------------------------------------------
# Schema Retrieval
# ------------------------------------------------------

SCHEMA_RETRIEVAL_STRATEGY = (
    settings.schema_retrieval_strategy
)

# ------------------------------------------------------
# SQL Correction
# ------------------------------------------------------

SQL_CORRECTION_MAX_ATTEMPTS = (
    settings.sql_correction_max_attempts
)