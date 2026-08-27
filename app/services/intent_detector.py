import logging
import re

from app.models.intent import QueryIntent
from app.models.intent_analysis import IntentAnalysis


logger = logging.getLogger(__name__)


class IntentDetector:
    """
    Detects the user's query intent using deterministic
    weighted keyword and natural-language pattern scoring.

    The detector supports multi-intent questions such as:

        "Show total sales by month"

    which may contain:

        TIME_SERIES
        AGGREGATION
        GROUP_BY
        LOOKUP

    The highest-scoring intent becomes primary and all other
    positive-scoring intents become secondary.
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
        "give": 1,
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

        # Business-metric language
        "sales": 4,
        "revenue": 5,
        "spending": 5,
        "spent": 4,
        "amount": 4,
        "value": 3,
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
        "greatest": 4,
        "most": 3,
        "least": 3,

        # Recency / ordering
        "recent": 5,
        "recently": 5,
        "latest": 5,
        "newest": 5,
        "oldest": 5,
        "earliest": 5,
    }

    TIME_KEYWORDS = {
        "monthly": 5,
        "month": 5,
        "months": 5,

        "daily": 4,
        "day": 4,
        "days": 4,

        "weekly": 4,
        "week": 4,
        "weeks": 4,

        "yearly": 5,
        "year": 5,
        "years": 5,

        "trend": 5,
        "trends": 5,
        "history": 4,
        "time": 4,
    }

    COMPARISON_KEYWORDS = {
        "compare": 5,
        "comparison": 5,
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

    TIME_SERIES_PATTERNS = (
        r"\bby\s+month\b",
        r"\bper\s+month\b",
        r"\beach\s+month\b",

        r"\bby\s+day\b",
        r"\bper\s+day\b",
        r"\beach\s+day\b",

        r"\bby\s+week\b",
        r"\bper\s+week\b",
        r"\beach\s+week\b",

        r"\bby\s+year\b",
        r"\bper\s+year\b",
        r"\beach\s+year\b",

        r"\bover\s+time\b",
        r"\bover\s+the\s+time\b",
        r"\bthrough\s+time\b",
        r"\bpurchase\s+history\b",
        r"\border\s+history\b",
        r"\bsales\s+trend(?:s)?\b",
    )

    GROUP_BY_PATTERNS = (
        r"\bby\s+month\b",
        r"\bby\s+day\b",
        r"\bby\s+week\b",
        r"\bby\s+year\b",
        r"\bper\s+\w+\b",
        r"\bfor\s+each\s+\w+\b",
    )

    AGGREGATION_PATTERNS = (
        r"\btotal\s+\w+",
        r"\bsales\s+(?:amount|value|activity)\b",
        r"\brevenue\b",
        r"\bspending\b",
        r"\bspent\b",
        r"\bpurchase\s+value\b",
        r"\btransaction\s+value\b",
        r"\bnumber\s+of\b",
    )

    SORT_PATTERNS = (
        r"\bmost\s+recent\b",
        r"\bspent\s+the\s+most\b",
        r"\bhighest\s+\w+",
        r"\blargest\s+\w+",
        r"\bgreatest\s+\w+",
        r"\bsmallest\s+\w+",
        r"\blowest\s+\w+",
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

    @staticmethod
    def _tokenize(
        question: str,
    ) -> set[str]:
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
        Detect primary and secondary query intents.
        """

        if not question or not question.strip():

            return IntentAnalysis(
                primary=QueryIntent.UNKNOWN,
                secondary=[],
                scores=self._empty_scores(),
                confidence=0.0,
            )

        question = question.strip()

        tokens = self._tokenize(
            question
        )

        scores = self._score_intents(
            tokens=tokens,
            question=question,
        )

        logger.debug(
            "Intent scores: %s",
            scores,
        )

        primary = self._best_intent(
            scores
        )

        secondary = self._secondary_intents(
            scores=scores,
            primary=primary,
        )

        confidence = self._confidence(
            scores
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
        Calculate weighted scores for all supported intents.
        """

        scores = self._empty_scores()

        scores[
            QueryIntent.LOOKUP
        ] += self._count_matches(
            tokens,
            self.LOOKUP_KEYWORDS,
        )

        scores[
            QueryIntent.AGGREGATION
        ] += self._count_matches(
            tokens,
            self.AGGREGATION_KEYWORDS,
        )

        scores[
            QueryIntent.GROUP_BY
        ] += self._count_matches(
            tokens,
            self.GROUP_BY_KEYWORDS,
        )

        scores[
            QueryIntent.SORT
        ] += self._count_matches(
            tokens,
            self.SORT_KEYWORDS,
        )

        scores[
            QueryIntent.TIME_SERIES
        ] += self._count_matches(
            tokens,
            self.TIME_KEYWORDS,
        )

        scores[
            QueryIntent.COMPARISON
        ] += self._count_matches(
            tokens,
            self.COMPARISON_KEYWORDS,
        )

        scores[
            QueryIntent.JOIN
        ] += self._count_matches(
            tokens,
            self.JOIN_KEYWORDS,
        )

        # --------------------------------------------------
        # Pattern bonuses
        # --------------------------------------------------

        if self._matches_any_pattern(
            question,
            self.LOOKUP_PATTERNS,
        ):
            scores[
                QueryIntent.LOOKUP
            ] += 3

        if self._matches_any_pattern(
            question,
            self.JOIN_PATTERNS,
        ):
            scores[
                QueryIntent.JOIN
            ] += 4

        if self._matches_any_pattern(
            question,
            self.TIME_SERIES_PATTERNS,
        ):
            scores[
                QueryIntent.TIME_SERIES
            ] += 5

        if self._matches_any_pattern(
            question,
            self.GROUP_BY_PATTERNS,
        ):
            scores[
                QueryIntent.GROUP_BY
            ] += 3

        if self._matches_any_pattern(
            question,
            self.AGGREGATION_PATTERNS,
        ):
            scores[
                QueryIntent.AGGREGATION
            ] += 4

        if self._matches_any_pattern(
            question,
            self.SORT_PATTERNS,
        ):
            scores[
                QueryIntent.SORT
            ] += 4

        return scores

    # ======================================================
    # EMPTY SCORE MAP
    # ======================================================

    @staticmethod
    def _empty_scores(
    ) -> dict[QueryIntent, int]:

        return {
            QueryIntent.LOOKUP: 0,
            QueryIntent.AGGREGATION: 0,
            QueryIntent.GROUP_BY: 0,
            QueryIntent.SORT: 0,
            QueryIntent.TIME_SERIES: 0,
            QueryIntent.COMPARISON: 0,
            QueryIntent.JOIN: 0,
        }

    # ======================================================
    # KEYWORD MATCHING
    # ======================================================

    @staticmethod
    def _count_matches(
        tokens: set[str],
        keywords: dict[str, int],
    ) -> int:
        """
        Calculate a weighted keyword score.
        """

        return sum(
            keywords.get(
                token,
                0,
            )
            for token in tokens
        )

    # ======================================================
    # PATTERN MATCHING
    # ======================================================

    @staticmethod
    def _matches_any_pattern(
        question: str,
        patterns: tuple[str, ...],
    ) -> bool:
        """
        Return True if one of the supplied regex patterns
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
            scores.values(),
            default=0,
        )

        if max_score <= 0:
            return QueryIntent.UNKNOWN

        candidates = [
            intent
            for intent, score
            in scores.items()
            if score == max_score
        ]

        return max(
            candidates,
            key=lambda intent: (
                self.INTENT_PRIORITY.get(
                    intent,
                    0,
                )
            ),
        )

    # ======================================================
    # CONFIDENCE
    # ======================================================

    @staticmethod
    def _confidence(
        scores: dict[QueryIntent, int],
    ) -> float:
        """
        Calculate relative primary-intent confidence.
        """

        total = sum(
            scores.values()
        )

        if total <= 0:
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
        Return all positively scored non-primary intents,
        sorted by relevance and tie-breaking priority.
        """

        secondary = [
            intent
            for intent, score
            in scores.items()
            if (
                intent != primary
                and score > 0
            )
        ]

        return sorted(
            secondary,
            key=lambda intent: (
                scores[intent],
                self.INTENT_PRIORITY.get(
                    intent,
                    0,
                ),
            ),
            reverse=True,
        )