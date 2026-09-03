from __future__ import annotations

import math
from threading import RLock

from app.cache.semantic_cache_entry import SemanticSQLCacheEntry


class SemanticSQLCache:
    """
    Thread-safe bounded in-memory semantic SQL cache.

    This class is responsible only for:
    - storing semantic cache entries
    - cosine-similarity search
    - bounded eviction
    - basic cache metrics

    It does NOT decide whether a semantic match is safe to reuse.
    Intent/schema/query compatibility belongs to the service layer.
    """

    def __init__(
        self,
        max_size: int = 256,
        similarity_threshold: float = 0.95,
    ):
        if max_size <= 0:
            raise ValueError("max_size must be greater than 0")

        if not 0.0 <= similarity_threshold <= 1.0:
            raise ValueError(
                "similarity_threshold must be between 0.0 and 1.0"
            )

        self.max_size = max_size
        self.similarity_threshold = similarity_threshold

        self._entries: list[SemanticSQLCacheEntry] = []
        self._lock = RLock()

        self._hits = 0
        self._misses = 0
        self._stores = 0
        self._evictions = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add(self, entry: SemanticSQLCacheEntry) -> None:
        self._validate_entry(entry)

        with self._lock:
            self._entries.append(entry)
            self._stores += 1

            while len(self._entries) > self.max_size:
                self._entries.pop(0)
                self._evictions += 1

    def search(
        self,
        embedding: tuple[float, ...],
    ) -> tuple[SemanticSQLCacheEntry, float] | None:
        self._validate_embedding(embedding)

        with self._lock:
            best_entry: SemanticSQLCacheEntry | None = None
            best_score = -1.0

            for entry in self._entries:
                if len(entry.embedding) != len(embedding):
                    continue

                score = self._cosine_similarity(
                    embedding,
                    entry.embedding,
                )

                if score > best_score:
                    best_score = score
                    best_entry = entry

            if (
                best_entry is None
                or best_score < self.similarity_threshold
            ):
                self._misses += 1
                return None

            self._hits += 1

            return best_entry, best_score

    def delete(self, entry: SemanticSQLCacheEntry) -> bool:
        with self._lock:
            try:
                self._entries.remove(entry)
            except ValueError:
                return False

            return True

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._entries)

    def stats(self) -> dict[str, int]:
        with self._lock:
            return {
                "size": len(self._entries),
                "hits": self._hits,
                "misses": self._misses,
                "stores": self._stores,
                "evictions": self._evictions,
            }

    def reset_stats(self) -> None:
        with self._lock:
            self._hits = 0
            self._misses = 0
            self._stores = 0
            self._evictions = 0

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_entry(
        entry: SemanticSQLCacheEntry,
    ) -> None:
        if not entry.question.strip():
            raise ValueError("question must not be empty")

        if not entry.sql.strip():
            raise ValueError("sql must not be empty")

        if not entry.embedding:
            raise ValueError("embedding must not be empty")

        SemanticSQLCache._validate_embedding(entry.embedding)

        if not entry.schema_fingerprint.strip():
            raise ValueError(
                "schema_fingerprint must not be empty"
            )

        if not entry.provider.strip():
            raise ValueError("provider must not be empty")

        if not entry.model.strip():
            raise ValueError("model must not be empty")

        if not entry.cache_version.strip():
            raise ValueError(
                "cache_version must not be empty"
            )

    @staticmethod
    def _validate_embedding(
        embedding: tuple[float, ...],
    ) -> None:
        if not embedding:
            raise ValueError("embedding must not be empty")

        for value in embedding:
            if not isinstance(value, (int, float)):
                raise ValueError(
                    "embedding values must be numeric"
                )

            if not math.isfinite(value):
                raise ValueError(
                    "embedding values must be finite"
                )

        magnitude = math.sqrt(
            sum(float(value) ** 2 for value in embedding)
        )

        if magnitude == 0.0:
            raise ValueError(
                "embedding must have non-zero magnitude"
            )

    # ------------------------------------------------------------------
    # Similarity
    # ------------------------------------------------------------------

    @staticmethod
    def _cosine_similarity(
        left: tuple[float, ...],
        right: tuple[float, ...],
    ) -> float:
        if len(left) != len(right):
            raise ValueError(
                "embedding dimensions must match"
            )

        dot_product = sum(
            float(a) * float(b)
            for a, b in zip(left, right)
        )

        left_norm = math.sqrt(
            sum(float(value) ** 2 for value in left)
        )

        right_norm = math.sqrt(
            sum(float(value) ** 2 for value in right)
        )

        if left_norm == 0.0 or right_norm == 0.0:
            raise ValueError(
                "embedding must have non-zero magnitude"
            )

        return dot_product / (left_norm * right_norm)