import re 
from app.models.intent import QueryIntent
from app.models.intent_analysis import IntentAnalysis

class IntentDetector:
    """
    Detects the user's query intent.
    """
    
    LOOKUP_KEYWORDS = {
        "show": 1,
        "list": 2,
        "display": 2,
        "find": 3,
        "get": 1,
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
    }
    
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

    def _tokenize(self, question: str) -> set[str]:
        return set(re.findall(r'\b\w+\b', question.lower()))
            

    def detect(self, question: str,) -> IntentAnalysis:
        tokens = self._tokenize(question)
        scores = self._score_intents(tokens)
        logger.debug(f"Intent scores: {scores}")
        primary = self._best_intent(scores)
        confidence = self._confidence(scores)
        secondary = self._secondary_intents(scores, primary)
        return IntentAnalysis(primary=primary, secondary=secondary, scores=scores, confidence=confidence)

    def _score_intents(self, tokens: set[str],) -> dict[QueryIntent, int]:
        """
        Score each intent based on the number of matching keywords.
        """
        return {
            QueryIntent.LOOKUP: self._count_matches(tokens, self.LOOKUP_KEYWORDS),
            QueryIntent.AGGREGATION: self._count_matches(tokens, self.AGGREGATION_KEYWORDS),
            QueryIntent.GROUP_BY: self._count_matches(tokens, self.GROUP_BY_KEYWORDS),
            QueryIntent.SORT: self._count_matches(tokens, self.SORT_KEYWORDS),
            QueryIntent.TIME_SERIES: self._count_matches(tokens, self.TIME_KEYWORDS),
            QueryIntent.COMPARISON: self._count_matches(tokens, self.COMPARISON_KEYWORDS),
            QueryIntent.JOIN: self._count_matches(tokens, self.JOIN_KEYWORDS),
        }

    def _count_matches(self, tokens: set[str], keywords: dict[str, int]) -> int:
        """
        Calculate the weighted score for an intent.       
        """
        score = 0
        for token in tokens:
            score += keywords.get(token, 0)
        return score

    def _best_intent(self, scores: dict[QueryIntent, int]) -> QueryIntent:
        """
        Return the highest-scoring intent.
        If multiple intents have the same score,
        resolve the tie using INTENT_PRIORITY.
        """
        max_score = max(scores.values())
        if max_score == 0:
            return QueryIntent.UNKNOWN
        candidates = [intent for intent, score in scores.items() if score == max_score]
        return max(candidates, key=lambda intent: self.INTENT_PRIORITY[intent])
    
    def _confidence(self, scores: dict[QueryIntent, int]) -> float:
        """
        Calculate confidence as the ratio of the best score to the sum of all scores.
        """
        total = sum(scores.values())
        if total == 0:
            return 0.0
        best = max(scores.values())
        return round(best / total, 2)
    
    def _secondary_intents(self, scores: dict[QueryIntent, int], primary: QueryIntent) -> list[QueryIntent]:
        """
        Return a list of secondary intents sorted by score, excluding the primary intent.
        """
        secondary = []
        for intent, score in scores.items():
            if intent == primary:
                continue
            if score > 0:
                secondary.append(intent)
        return sorted(secondary, key=lambda intent: (scores[intent], self.INTENT_PRIORITY[intent]), reverse=True)