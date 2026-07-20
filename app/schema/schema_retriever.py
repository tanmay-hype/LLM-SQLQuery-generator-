from app.schema.retrievers.keyword_retriever import KeywordRetriever


class SchemaRetriever:
    """
    Coordinates schema retrieval strategies.
    """

    def __init__(self):

        self.keyword_retriever = KeywordRetriever()

    def retrieve(
        self,
        schema: dict,
        question: str,
    ) -> dict:
        """
        Retrieve the relevant schema using the configured strategy.
        """

        return self.keyword_retriever.retrieve(
            schema=schema,
            question=question,
        )