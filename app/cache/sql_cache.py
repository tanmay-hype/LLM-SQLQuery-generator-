import hashlib
import json
import logging
import re
from collections import OrderedDict
from threading import RLock

from app.cache.base import BaseSQLCache


logger = logging.getLogger(__name__)


class SQLCache(BaseSQLCache):
    """
    Thread-safe bounded in-memory LRU cache for validated SQL.

    This cache stores final validated SQL, not raw LLM output.
    """

    def __init__(
        self,
        max_size: int = 256,
    ):
        if max_size <= 0:
            raise ValueError(
                "SQL cache max_size must be greater than 0."
            )

        self.max_size = max_size

        self._cache: OrderedDict[
            str,
            str,
        ] = OrderedDict()

        self._lock = RLock()
        
        # ==================================================
        # CACHE METRICS
        # ==================================================
        
        self._hits = 0
        self._misses = 0
        self._stores = 0
        self._evictions = 0

    # ======================================================
    # KEY GENERATION
    # ======================================================

    @staticmethod
    def normalize_question(
        question: str,
    ) -> str:
        """
        Normalize harmless formatting differences in a
        natural-language question.

        Example:

            "  Show   all CUSTOMERS "
                ->
            "show all customers"
        """

        normalized = question.strip().lower()

        normalized = re.sub(
            r"\s+",
            " ",
            normalized,
        )

        return normalized

    @classmethod
    def build_key(
        cls,
        question: str,
        schema_fingerprint: str,
        provider: str,
        model: str,
    ) -> str:
        """
        Build a deterministic cache key.

        Schema fingerprint is included so SQL generated
        for an old schema is not reused after the schema
        changes.
        """

        if not question.strip():
            raise ValueError(
                "Question cannot be empty."
            )

        if not schema_fingerprint:
            raise ValueError(
                "Schema fingerprint cannot be empty."
            )

        normalized_question = (
            cls.normalize_question(
                question
            )
        )

        payload = {
            "question": normalized_question,
            "schema_fingerprint": (
                schema_fingerprint
            ),
            "provider": (
                provider.strip().lower()
            ),
            "model": (
                model.strip().lower()
            ),
        }

        serialized = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        )

        return hashlib.sha256(
            serialized.encode("utf-8")
        ).hexdigest()

    # ======================================================
    # CACHE OPERATIONS
    # ======================================================

    def get(
        self,
        key: str,
    ) -> str | None:
        with self._lock:

            sql = self._cache.get(
                key
            )

            if sql is None:
                self._misses += 1
                logger.debug(
                    "SQL cache miss."
                )
                return None
            
            self._hits += 1

            # Mark entry as recently used.
            self._cache.move_to_end(
                key
            )

            logger.debug(
                "SQL cache hit."
            )

            return sql

    def set(
        self,
        key: str,
        sql: str,
    ) -> None:
        if not key:
            raise ValueError(
                "SQL cache key cannot be empty."
            )

        if not sql or not sql.strip():
            raise ValueError(
                "Cached SQL cannot be empty."
            )

        with self._lock:

            self._cache[key] = sql.strip()

            # Newly inserted/updated entry becomes MRU.
            self._cache.move_to_end(
                key
            )
            
            self._stores += 1
            
            # Remove least recently used entries.
            while (
                len(self._cache)
                > self.max_size
            ):
                self._cache.popitem(
                    last=False
                )
                
                self._evictions += 1
                
            logger.debug(
                "SQL cached successfully."
            )

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()

        logger.debug(
            "SQL cache cleared."
        )

    def __len__(self) -> int:
        with self._lock:
            return len(
                self._cache
            )
            
    # ======================================================
    # CACHE METRICS
    # ======================================================
    
    def stats(self) -> dict:
        """Return cache statistics."""
        
        with self._lock:
            
            requests = (
                self._hits
                + self._misses
            )
            
            hit_rate = (
                self._hits / requests
                if requests > 0
                else 0.0
            )
            
            return {
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": hit_rate,
                "stores": self._stores,
                "evictions": self._evictions,
                "current_size": len(self._cache),
                "max_size": self.max_size,
                "hit_rate": hit_rate,
            }
            
    def reset_stats(self) -> None:
        """Reset cache statistics."""
        
        with self._lock:
            self._hits = 0
            self._misses = 0
            self._stores = 0
            self._evictions = 0
            
        logger.debug(
            "SQL cache statistics reset."
        )