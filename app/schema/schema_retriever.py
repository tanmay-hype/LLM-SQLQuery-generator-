from app.schema.retrievers.keywords_retriever import KeywordsRetriever
from app.schema.models.retrieval_result import RetrievalResult

class SchemaRetriever:
    """
    Coordinates schema retrieval strategies.
    """

    def __init__(self):
        self.keyword_retriever = KeywordsRetriever()

    def retrieve(
        self,
        schema: dict,
        question: str,
    ) -> RetrievalResult:
        """
        Retrieve the relevant schema using the configured strategy.
        """
        result = self.keyword_retriever.retrieve(
            schema=schema,
            question=question,
        )
    
        return result.schema
