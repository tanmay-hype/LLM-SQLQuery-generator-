from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import schema

from app.cache.semantic_cache_entry import SemanticSQLCacheEntry
from app.cache.semantic_sql_cache import SemanticSQLCache
from app.cache.semantic_sql_cache_compatibility import (
    SemanticSQLCacheCompatibility,
)
from app.models.intent_analysis import IntentAnalysis


class SemanticSQLCacheService:
    """
    Coordinates safe semantic SQL cache lookup and storage.

    Responsibilities:
    - obtain embeddings
    - perform metadata-filtered semantic search
    - enforce deterministic compatibility
    - store validated SQL

    This service does NOT validate SQL itself.
    QueryService remains responsible for structural and semantic
    validation before executing a semantic-cache hit.
    """

    def __init__(
        self,
        cache: SemanticSQLCache,
        embedding_service,
        compatibility: SemanticSQLCacheCompatibility | None = None,
    ):
        self.cache = cache
        self.embedding_service = embedding_service
        self.compatibility = (
            compatibility
            or SemanticSQLCacheCompatibility()
        )

    def lookup(
        self,
        *,
        question: str,
        intent: IntentAnalysis,
        schema_fingerprint: str,
        provider: str,
        model: str,
        cache_version: str,
    ) -> tuple[SemanticSQLCacheEntry, float] | None:
        self._validate_context(
            question=question,
            schema_fingerprint=schema_fingerprint,
            provider=provider,
            model=model,
            cache_version=cache_version,
        )

        embedding = self._embed(question)

        result = self.cache.search(
            embedding,
            schema_fingerprint=schema_fingerprint,
            provider=provider,
            model=model,
            cache_version=cache_version,
        )

        if result is None:
            return None

        entry, score = result

        if not self.compatibility.is_compatible(
            question,
            intent,
            entry,
            schema = schema,
        ):
            return None

        return entry, score

    def store(
        self,
        *,
        question: str,
        sql: str,
        intent: IntentAnalysis,
        schema_fingerprint: str,
        provider: str,
        model: str,
        cache_version: str,
    ) -> SemanticSQLCacheEntry:
        self._validate_context(
            question=question,
            schema_fingerprint=schema_fingerprint,
            provider=provider,
            model=model,
            cache_version=cache_version,
        )

        if not sql.strip():
            raise ValueError("sql must not be empty")

        embedding = self._embed(question)

        entry = SemanticSQLCacheEntry(
            question=question.strip(),
            sql=sql.strip(),
            embedding=embedding,
            schema_fingerprint=schema_fingerprint.strip(),
            provider=provider.strip(),
            model=model.strip(),
            cache_version=cache_version.strip(),
            primary_intent=intent.primary,
            secondary_intents=tuple(intent.secondary),
        )

        self.cache.add(entry)

        return entry

    def delete(
        self,
        entry: SemanticSQLCacheEntry,
    ) -> bool:
        return self.cache.delete(entry)

    def _embed(
        self,
        text: str,
    ) -> tuple[float, ...]:
        results = (
           self.embedding_service.create_embeddings(
            [text]
           )
        )

        if len(results) != 1:
           raise RuntimeError(
                 "embedding service must return exactly "
                 "one embedding for one input text"
           )

        embedding = results[0]

        if not isinstance(
           embedding,
           Sequence,
        ) or isinstance(
           embedding,
           (str, bytes),
        ):
            raise TypeError(
                "embedding service must return "
                "a numeric sequence"
            )
        

        if not embedding:
            raise ValueError(
                "embedding service returned "
                "an empty embedding"
        )

        return tuple(
            float(value)
            for value in embedding
        )

    @staticmethod
    def _validate_context(
        *,
        question: str,
        schema_fingerprint: str,
        provider: str,
        model: str,
        cache_version: str,
    ) -> None:
        values = {
            "question": question,
            "schema_fingerprint": schema_fingerprint,
            "provider": provider,
            "model": model,
            "cache_version": cache_version,
        }

        for name, value in values.items():
            if not value.strip():
                raise ValueError(
                    f"{name} must not be empty"
                )