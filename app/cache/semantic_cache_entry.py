from dataclasses import dataclass

from app.models.intent import QueryIntent


@dataclass(frozen=True)
class SemanticSQLCacheEntry:
    question: str
    sql: str
    embedding: tuple[float, ...]

    schema_fingerprint: str
    provider: str
    model: str
    cache_version: str

    primary_intent: QueryIntent
    secondary_intents: tuple[QueryIntent, ...]