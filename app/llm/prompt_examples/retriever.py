class ExampleRetriever:
    
    PRIMARY_WEIGHT = 5
    SECONDARY_WEIGHT = 2
    
    scored = [item for item in scored if item[0]>= self.MIN_SCORE]
    for example in self.repository.get_examples():
        score = self._score_example(example, analysis)
        scored.append((example, score))
    
    def __init__(self, repository: ExampleRepository):
        self.repository = repository

    def retrieve(self, question: str, intent: QueryIntent, top_k: int = EXAMPLE_RETRIEVER_TOP_K) -> list[PromptExample]:
        """
        Retrieves the most relevant prompt examples based on the input question and intent.
        """
        return [ example for example in self.repository.get_examples() if example.intents & {intent.primary} ][:top_k]
    
    def _score_example(self, example: PromptExample, analysis: IntentAnalysis) -> int:
        score = 0
        if analysis.primary in example.intents:
            score += self.PRIMARY_WEIGHT
        for intent in analysis.secondary:
            if intent in example.intents:
                score += self.SECONDARY_WEIGHT
                scored.sort(key=lambda item: item[1], reverse=True)
        return [example for _, example in scored[: self.MAX_EXAMPLES]]