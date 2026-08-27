from collections import OrderedDict
from threading import Lock

from google import genai

from app.core.config import settings
from app.schema.embeddings.base import EmbeddingService


class GeminiEmbeddingService(EmbeddingService):
    """
    Gemini embedding implementation with a bounded
    in-memory embedding cache.

    The cache reduces repeated Gemini API calls for
    identical texts.

    This is especially useful for repeated natural-language
    questions and retrieval benchmarks.

    The cache is process-local and intentionally not
    persisted to disk.
    """

    def __init__(self):
        if not settings.gemini_api_key:
            raise ValueError(
                "GEMINI_API_KEY is not configured."
            )

        self.client = genai.Client(
            api_key=settings.gemini_api_key,
        )

        # --------------------------------------------------
        # Embedding cache
        # --------------------------------------------------

        self._cache: OrderedDict[
            str,
            list[float],
        ] = OrderedDict()

        self._cache_lock = Lock()

        self._cache_max_size = (
            settings.embedding_cache_size
        )

    # ======================================================
    # PUBLIC API
    # ======================================================

    def create_embeddings(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        """
        Generate embeddings for the supplied texts.

        Cached embeddings are reused whenever possible.

        Any texts missing from the cache are embedded in
        one Gemini batch request.

        Returned embeddings preserve the exact same order
        as the supplied texts.
        """

        if not texts:
            return []

        # --------------------------------------------------
        # Validate input
        # --------------------------------------------------

        for text in texts:

            if not isinstance(text, str):
                raise ValueError(
                    "Embedding input must contain only strings."
                )

            if not text.strip():
                raise ValueError(
                    "Embedding input cannot contain empty text."
                )

        # --------------------------------------------------
        # Build cache keys
        # --------------------------------------------------

        keys = [
            self._cache_key(text)
            for text in texts
        ]

        cached_results: dict[
            str,
            list[float],
        ] = {}

        missing_by_key: dict[
            str,
            str,
        ] = {}

        # --------------------------------------------------
        # Check cache
        # --------------------------------------------------

        with self._cache_lock:

            for text, key in zip(
                texts,
                keys,
            ):

                if key in self._cache:

                    cached_results[
                        key
                    ] = self._cache[
                        key
                    ]

                    # Mark as recently used.
                    self._cache.move_to_end(
                        key
                    )

                else:

                    # Deduplicate identical missing texts
                    # within the same request.
                    if key not in missing_by_key:
                        missing_by_key[
                            key
                        ] = text

        # ==================================================
        # GEMINI API CALL FOR CACHE MISSES
        # ==================================================

        if missing_by_key:

            missing_keys = list(
                missing_by_key.keys()
            )

            missing_texts = [
                missing_by_key[key]
                for key in missing_keys
            ]

            response = (
                self.client.models.embed_content(
                    model=(
                        settings.gemini_embedding_model
                    ),
                    contents=missing_texts,
                )
            )

            embeddings = [
                embedding.values
                for embedding
                in response.embeddings
            ]

            if (
                len(embeddings)
                != len(missing_texts)
            ):
                raise RuntimeError(
                    "Gemini returned an unexpected "
                    "number of embeddings."
                )

            # --------------------------------------------------
            # Store new embeddings
            # --------------------------------------------------

            with self._cache_lock:

                for key, embedding in zip(
                    missing_keys,
                    embeddings,
                ):

                    self._cache[
                        key
                    ] = embedding

                    self._cache.move_to_end(
                        key
                    )

                    cached_results[
                        key
                    ] = embedding

                self._evict_if_needed()

        # ==================================================
        # RETURN IN ORIGINAL ORDER
        # ==================================================

        return [
            cached_results[key]
            for key in keys
        ]

    # ======================================================
    # CACHE HELPERS
    # ======================================================

    @staticmethod
    def _cache_key(
        text: str,
    ) -> str:
        """
        Build a stable cache key.

        Only insignificant whitespace is normalized.

        Case is intentionally preserved because the
        embedding provider receives the original text.
        """

        return " ".join(
            text.split()
        )

    # ------------------------------------------------------

    def _evict_if_needed(
        self,
    ) -> None:
        """
        Remove least-recently-used entries once the
        configured cache capacity has been exceeded.

        Must be called while holding _cache_lock.
        """

        while (
            len(self._cache)
            > self._cache_max_size
        ):

            self._cache.popitem(
                last=False
            )

    # ======================================================
    # CACHE MANAGEMENT
    # ======================================================

    def clear_cache(
        self,
    ) -> None:
        """
        Clear all cached embeddings.

        Primarily useful for tests and maintenance.
        """

        with self._cache_lock:
            self._cache.clear()

    # ------------------------------------------------------

    @property
    def cache_size(
        self,
    ) -> int:
        """
        Return the current number of cached embeddings.
        """

        with self._cache_lock:
            return len(
                self._cache
            )