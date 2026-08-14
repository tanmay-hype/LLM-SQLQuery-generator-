import re
import logging

from app.models.intent import QueryIntent
from app.models.intent_analysis import IntentAnalysis


logger = logging.getLogger(__name__)


class IntentDetector:
    """
    Detects the user's query intent.

    The detector uses a lightweight rule-based scoring system.
    It combines:

    1. Explicit intent keywords
    2. Natural-language question patterns
    3. Relationship / join patterns
    4. Intent priority for tie-breaking

    The detector does not generate SQL.
    It only describes what the user is trying to do.
    """

    # ======================================================
    # EXPLICIT KEYWORDS
    # ======================================================

    LOOKUP_KEYWORDS = {
        "show": 1,
        "list": 2,
        "display": 2,
        "find": 3,
        "get": 1,

        # Natural-language lookup questions
        "which": 3,
        "what": 3,
        "who": 3,
        "where": 2,
        "when": 2,
    }

    AGGREGATION_KEYWORDS = {
        "sum": 5,
        "total": 4,
        "average": 5,
        "avg": 5,
        "count": 5,
        "maximum": 5,
        "minimum": 5,
        "max": 5,
        "min": 5,
    }

    GROUP_BY_KEYWORDS = {
        "per": 3,
        "group": 4,
        "each": 2,
        "by": 1,
    }

    SORT_KEYWORDS = {
        "top": 5,
        "highest": 5,
        "lowest": 5,
        "largest": 4,
        "smallest": 4,
        
        #Recency / ordering
        "recent": 5,
        "recently": 5,
        "latest": 5,
        "newest": 5,
        "oldest": 5,
        "earliest": 5,
    }

    TIME_KEYWORDS = {
        "monthly": 5,
        "daily": 4,
        "weekly": 4,
        "yearly": 5,
        "trend": 5,
    }

    COMPARISON_KEYWORDS = {
        "compare": 5,
        "versus": 5,
        "vs": 5,
    }

    JOIN_KEYWORDS = {
        "with": 2,
        "along": 2,
        "including": 3,
        "associated": 3,
        "related": 3,
        "belong": 3,
    }

    # ======================================================
    # NATURAL LANGUAGE PATTERNS
    # ======================================================

    LOOKUP_PATTERNS = (
        r"^which\b",
        r"^what\b",
        r"^who\b",
        r"^where\b",
        r"^when\b",
        r"\bwhich\s+\w+",
        r"\bwhat\s+\w+",
    )

    JOIN_PATTERNS = (
        r"\bwere\s+ordered\b",
        r"\bwas\s+ordered\b",
        r"\bhave\s+placed\s+orders?\b",
        r"\bhas\s+placed\s+orders?\b",
        r"\bplaced\s+orders?\b",
        r"\bordered\s+by\b",
        r"\bpurchased\s+by\b",
        r"\bbought\s+by\b",
        r"\bassociated\s+with\b",
        r"\brelated\s+to\b",
        r"\bbelong(?:s)?\s+to\b",
    )

    # ======================================================
    # INTENT PRIORITY
    # ======================================================

    INTENT_PRIORITY = {
        QueryIntent.TIME_SERIES: 7,
        QueryIntent.AGGREGATION: 6,
        QueryIntent.COMPARISON: 5,
        QueryIntent.GROUP_BY: 4,
        QueryIntent.JOIN: 3,
        QueryIntent.SORT: 2,
        QueryIntent.LOOKUP: 1,
        QueryIntent.UNKNOWN: 0,
    }

    # ======================================================
    # TOKENIZATION
    # ======================================================

    def _tokenize(self, question: str) -> set[str]:
        """
        Convert the question into normalized tokens.
        """

        return set(
            re.findall(
                r"\b\w+\b",
                question.lower(),
            )
        )

    # ======================================================
    # PUBLIC API
    # ======================================================

    def detect(
        self,
        question: str,
    ) -> IntentAnalysis:
        """
        Detect the primary and secondary intents.
        """

        if not question or not question.strip():
            return IntentAnalysis(
                primary=QueryIntent.UNKNOWN,
                secondary=[],
                scores={
                    QueryIntent.LOOKUP: 0,
                    QueryIntent.AGGREGATION: 0,
                    QueryIntent.GROUP_BY: 0,
                    QueryIntent.SORT: 0,
                    QueryIntent.TIME_SERIES: 0,
                    QueryIntent.COMPARISON: 0,
                    QueryIntent.JOIN: 0,
                },
                confidence=0.0,
            )

        question = question.strip()

        tokens = self._tokenize(question)

        scores = self._score_intents(
            tokens=tokens,
            question=question,
        )

        logger.debug(
            "Intent scores: %s",
            scores,
        )

        primary = self._best_intent(scores)

        confidence = self._confidence(
            scores
        )

        secondary = self._secondary_intents(
            scores=scores,
            primary=primary,
        )

        logger.debug(
            "Detected primary intent: %s",
            primary,
        )

        logger.debug(
            "Detected secondary intents: %s",
            secondary,
        )

        return IntentAnalysis(
            primary=primary,
            secondary=secondary,
            scores=scores,
            confidence=confidence,
        )

    # ======================================================
    # INTENT SCORING
    # ======================================================

    def _score_intents(
        self,
        tokens: set[str],
        question: str,
    ) -> dict[QueryIntent, int]:
        """
        Calculate scores for every supported intent.
        """

        scores = {
            QueryIntent.LOOKUP: self._count_matches(
                tokens,
                self.LOOKUP_KEYWORDS,
            ),

            QueryIntent.AGGREGATION: self._count_matches(
                tokens,
                self.AGGREGATION_KEYWORDS,
            ),

            QueryIntent.GROUP_BY: self._count_matches(
                tokens,
                self.GROUP_BY_KEYWORDS,
            ),

            QueryIntent.SORT: self._count_matches(
                tokens,
                self.SORT_KEYWORDS,
            ),

            QueryIntent.TIME_SERIES: self._count_matches(
                tokens,
                self.TIME_KEYWORDS,
            ),

            QueryIntent.COMPARISON: self._count_matches(
                tokens,
                self.COMPARISON_KEYWORDS,
            ),

            QueryIntent.JOIN: self._count_matches(
                tokens,
                self.JOIN_KEYWORDS,
            ),
        }

        # --------------------------------------------------
        # Natural-language lookup patterns
        # --------------------------------------------------

        if self._matches_any_pattern(
            question,
            self.LOOKUP_PATTERNS,
        ):
            scores[QueryIntent.LOOKUP] += 3

        # --------------------------------------------------
        # Relationship / JOIN patterns
        # --------------------------------------------------

        if self._matches_any_pattern(
            question,
            self.JOIN_PATTERNS,
        ):
            scores[QueryIntent.JOIN] += 4

        return scores

    # ======================================================
    # KEYWORD MATCHING
    # ======================================================

    @staticmethod
    def _count_matches(
        tokens: set[str],
        keywords: dict[str, int],
    ) -> int:
        """
        Calculate weighted keyword score.
        """

        score = 0

        for token in tokens:
            score += keywords.get(
                token,
                0,
            )

        return score

    # ======================================================
    # PATTERN MATCHING
    # ======================================================

    @staticmethod
    def _matches_any_pattern(
        question: str,
        patterns: tuple[str, ...],
    ) -> bool:
        """
        Return True when at least one regex pattern
        matches the question.
        """

        return any(
            re.search(
                pattern,
                question,
                re.IGNORECASE,
            )
            for pattern in patterns
        )

    # ======================================================
    # PRIMARY INTENT
    # ======================================================

    def _best_intent(
        self,
        scores: dict[QueryIntent, int],
    ) -> QueryIntent:
        """
        Return the highest-scoring intent.

        Ties are resolved using INTENT_PRIORITY.
        """

        max_score = max(
            scores.values()
        )

        if max_score == 0:
            return QueryIntent.UNKNOWN

        candidates = [
            intent
            for intent, score in scores.items()
            if score == max_score
        ]

        return max(
            candidates,
            key=lambda intent: self.INTENT_PRIORITY[intent],
        )

    # ======================================================
    # CONFIDENCE
    # ======================================================

    def _confidence(
        self,
        scores: dict[QueryIntent, int],
    ) -> float:
        """
        Calculate confidence as:

            best score / total score
        """

        total = sum(
            scores.values()
        )

        if total == 0:
            return 0.0

        best = max(
            scores.values()
        )

        return round(
            best / total,
            2,
        )

    # ======================================================
    # SECONDARY INTENTS
    # ======================================================

    def _secondary_intents(
        self,
        scores: dict[QueryIntent, int],
        primary: QueryIntent,
    ) -> list[QueryIntent]:
        """
        Return all non-primary intents
        with a score greater than zero.

        Results are sorted by:

        1. Score
        2. Intent priority
        """

        secondary = []

        for intent, score in scores.items():

            if intent == primary:
                continue

            if score > 0:
                secondary.append(
                    intent
                )

        return sorted(
            secondary,
            key=lambda intent: (
                scores[intent],
                self.INTENT_PRIORITY[intent],
            ),
            reverse=True,
        )