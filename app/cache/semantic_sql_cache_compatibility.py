from __future__ import annotations

import re
from dataclasses import dataclass

from app.cache.semantic_cache_entry import SemanticSQLCacheEntry
from app.models.intent_analysis import IntentAnalysis


@dataclass(frozen=True)
class QuestionSignature:
    numeric_literals: tuple[str, ...]
    quoted_literals: tuple[str, ...]

    comparison: str | None
    ranking_direction: str | None
    temporal_direction: str | None

    has_negation: bool
    has_between: bool


class SemanticSQLCacheCompatibility:
    """
    Deterministic safety gate for semantic SQL cache reuse.

    Similarity answers:
        "Are these questions semantically close?"

    This class answers:
        "Did anything SQL-significant change?"
    """

    _NUMBER_PATTERN = re.compile(
        r"(?<![\w.])-?\d+(?:\.\d+)?(?![\w.])"
    )

    _QUOTED_PATTERN = re.compile(
        r"""['"]([^'"]+)['"]"""
    )

    _NEGATION_PATTERN = re.compile(
        r"\b(?:not|isn't|aren't|wasn't|weren't|without|except)\b",
        re.IGNORECASE,
    )

    _BETWEEN_PATTERN = re.compile(
        r"\bbetween\b",
        re.IGNORECASE,
    )

    _COMPARISON_PATTERNS = (
        (
            ">=",
            re.compile(
                r"\b(?:greater than or equal to|"
                r"at least|no less than)\b",
                re.IGNORECASE,
            ),
        ),
        (
            "<=",
            re.compile(
                r"\b(?:less than or equal to|"
                r"at most|no more than)\b",
                re.IGNORECASE,
            ),
        ),
        (
            "!=",
            re.compile(
                r"\b(?:not equal to|different from)\b",
                re.IGNORECASE,
            ),
        ),
        (
            ">",
            re.compile(
                r"\b(?:greater than|more than|above|over)\b",
                re.IGNORECASE,
            ),
        ),
        (
            "<",
            re.compile(
                r"\b(?:less than|fewer than|below|under)\b",
                re.IGNORECASE,
            ),
        ),
        (
            "=",
            re.compile(
                r"\b(?:equal to|equals|exactly)\b",
                re.IGNORECASE,
            ),
        ),
    )

    _ASCENDING_RANKING = re.compile(
        r"\b(?:cheapest|lowest|smallest|least expensive)\b",
        re.IGNORECASE,
    )

    _DESCENDING_RANKING = re.compile(
        r"\b(?:most expensive|highest|largest|top)\b",
        re.IGNORECASE,
    )

    _NEWEST_TEMPORAL = re.compile(
        r"\b(?:latest|newest|most recent|recent)\b",
        re.IGNORECASE,
    )

    _OLDEST_TEMPORAL = re.compile(
        r"\b(?:oldest|earliest|least recent)\b",
        re.IGNORECASE,
    )

    def is_compatible(
        self,
        question: str,
        intent: IntentAnalysis,
        entry: SemanticSQLCacheEntry,
    ) -> bool:
        if not question.strip():
            return False

        if intent.primary != entry.primary_intent:
            return False

        if set(intent.secondary) != set(entry.secondary_intents):
            return False

        current = self.build_signature(question)
        cached = self.build_signature(entry.question)

        if current.numeric_literals != cached.numeric_literals:
            return False

        if current.quoted_literals != cached.quoted_literals:
            return False

        if current.comparison != cached.comparison:
            return False

        if current.ranking_direction != cached.ranking_direction:
            return False

        if current.temporal_direction != cached.temporal_direction:
            return False

        if current.has_negation != cached.has_negation:
            return False

        if current.has_between != cached.has_between:
            return False

        return True

    def build_signature(
        self,
        question: str,
    ) -> QuestionSignature:
        normalized = self._normalize(question)

        return QuestionSignature(
            numeric_literals=self._extract_numeric_literals(
                normalized
            ),
            quoted_literals=self._extract_quoted_literals(
                normalized
            ),
            comparison=self._extract_comparison(normalized),
            ranking_direction=self._extract_ranking_direction(
                normalized
            ),
            temporal_direction=self._extract_temporal_direction(
                normalized
            ),
            has_negation=bool(
                self._NEGATION_PATTERN.search(normalized)
            ),
            has_between=bool(
                self._BETWEEN_PATTERN.search(normalized)
            ),
        )

    @staticmethod
    def _normalize(question: str) -> str:
        return " ".join(
            question.strip().lower().split()
        )

    def _extract_numeric_literals(
        self,
        question: str,
    ) -> tuple[str, ...]:
        return tuple(
            self._NUMBER_PATTERN.findall(question)
        )

    def _extract_quoted_literals(
        self,
        question: str,
    ) -> tuple[str, ...]:
        return tuple(
            value.strip().lower()
            for value in self._QUOTED_PATTERN.findall(question)
        )

    def _extract_comparison(
        self,
        question: str,
    ) -> str | None:
        for operator, pattern in self._COMPARISON_PATTERNS:
            if pattern.search(question):
                return operator

        return None

    def _extract_ranking_direction(
        self,
        question: str,
    ) -> str | None:
        if self._ASCENDING_RANKING.search(question):
            return "ASC"

        if self._DESCENDING_RANKING.search(question):
            return "DESC"

        return None

    def _extract_temporal_direction(
        self,
        question: str,
    ) -> str | None:
        if self._NEWEST_TEMPORAL.search(question):
            return "DESC"

        if self._OLDEST_TEMPORAL.search(question):
            return "ASC"

        return None