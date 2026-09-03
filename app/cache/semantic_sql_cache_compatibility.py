from __future__ import annotations

import re
from dataclasses import dataclass

from app.cache.semantic_cache_entry import SemanticSQLCacheEntry
from app.models.intent_analysis import IntentAnalysis


@dataclass(frozen=True)
class QuestionSignature:
    numeric_literals: tuple[str, ...]
    quoted_literals: tuple[str, ...]
    categorical_literals: tuple[str, ...]

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
    
    _CATEGORICAL_PATTERN = re.compile(
        r"\b(?:"
        r"(?:from|in)\s+(?!category\b)"
        r"([a-z][a-z0-9_-]*)"
        r"|"
        r"(?:in\s+)?category(?:\s+is)?\s+"
        r"([a-z][a-z0-9_-]*)"
        r")\b",
        re.IGNORECASE,
    )
    
    _SCHEMA_COLUMN_ALIASES = {
        "named": "name",
    }
    
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
        schema: dict | None = None,
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
        
        if( 
           current.categorical_literals != cached.categorical_literals
        ):
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
        
        if schema is not None:
            if not self._schema_values_compatible(
                current_question = question,
                cached_question = entry.question,
                schema = schema,
            ):
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
            categorical_literals=self._extract_categorical_literals(
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
    
    def _schema_values_compatible(
        self,
        *,
        current_question: str,
        cached_question: str,
        schema: dict,
    ) -> bool:
        """
        Check if the schema values in the current and cached questions are compatible.
        """
        current_values = self._extract_schema_values(
            current_question,
            schema,
        )

        cached_values = self._extract_schema_values(
            cached_question,
            schema,
        )

        return current_values == cached_values


    def _extract_schema_values(
        self,
        question: str,
        schema: dict,
    ) -> tuple[tuple[str, str], ...]:
        """
        Extract schema values from a question.
        """
        normalized = self._normalize(question)

        column_names = self._schema_column_names(schema)

        values: list[tuple[str, str]] = []

        for column_name in column_names:
            escaped_column = re.escape(column_name)

            patterns = (
                re.compile(
                    rf"\b{escaped_column}\s+is\s+"
                    rf"([^\s,?.]+)",
                    re.IGNORECASE,
                ),
                re.compile(
                    rf"\b(?:with|where)\s+"
                    rf"{escaped_column}\s+"
                    rf"([^\s,?.]+)",
                    re.IGNORECASE,
                ),
            )

            for pattern in patterns:
                match = pattern.search(normalized)

                if match is None:
                    continue

                value = match.group(1).strip().lower()

                if value:
                    values.append(
                       (
                           column_name,
                           value,
                        )
                  )

                break
        for alias, column_name in (
            self._SCHEMA_COLUMN_ALIASES.items()
        ):
            if column_name not in column_names:
               continue

            pattern = re.compile(
               rf"\b{re.escape(alias)}\s+"
               rf"(.+?)(?=$|\s+(?:with|where|and|or)\b)",
               re.IGNORECASE,
            )

            match = pattern.search(normalized)

            if match is None:
               continue

            value = match.group(1).strip().lower()

            if value:
                values.append(
                   (
                       column_name,
                       value,
                    )
                )

        return tuple(sorted(values))


    @staticmethod
    def _schema_column_names(
        schema: dict,
    ) -> tuple[str, ...]:
        names: set[str] = set()

        for table_data in schema.values():
            for column in table_data.get(
                "columns",
                [],
            ):
                name = column.get("name")

                if isinstance(name, str) and name.strip():
                    names.add(
                        name.strip().lower()
                    )

        return tuple(sorted(names))

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
    
    def _extract_categorical_literals(
        self,
        question: str,
    ) -> tuple[str, ...]:
        values = []
        
        for match in self._CATEGORICAL_PATTERN.findall(
            question
        ):
            value = next(
                (
                    item
                    for item in match 
                    if item 
                ),
                None,
            )
            
            if value is not None:
                values.append(value.strip().lower()
                )

        return tuple(values)

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