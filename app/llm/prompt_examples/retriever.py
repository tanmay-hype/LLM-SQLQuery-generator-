from app.core.config import settings
from app.llm.prompt_examples.repository import ExampleRepository
from app.models.intent_analysis import IntentAnalysis
from app.models.prompt_example import PromptExample


class ExampleRetriever:
    """
    Retrieves the most relevant few-shot examples based on
    the detected query intent.
    """

    PRIMARY_WEIGHT = 5
    SECONDARY_WEIGHT = 2

    MIN_SCORE = 3

    def __init__(self, repository: ExampleRepository):
        self.repository = repository

    def retrieve(
        self,
        analysis: IntentAnalysis,
        top_k: int = settings.example_retriever_top_k,
    ) -> list[PromptExample]:
        """
        Retrieve the highest-scoring prompt examples.
        """

        scored_examples: list[tuple[int, PromptExample]] = []

        for example in self.repository.get_examples():

            score = self._score_example(
                example,
                analysis,
            )

            if score >= self.MIN_SCORE:
                scored_examples.append(
                    (score, example)
                )

        scored_examples.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        return [
            example
            for _, example in scored_examples[:top_k]
        ]

    def _score_example(
        self,
        example: PromptExample,
        analysis: IntentAnalysis,
    ) -> int:
        """
        Compute a relevance score for one prompt example.
        """

        score = 0

        if analysis.primary in example.intents:
            score += self.PRIMARY_WEIGHT

        for intent in analysis.secondary:

            if intent in example.intents:
                score += self.SECONDARY_WEIGHT

        return score