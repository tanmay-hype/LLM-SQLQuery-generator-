from app.schema.models.retrieval_result import RetrievalResult
from app.schema.models.schema_document import SchemaDocument
from app.schema.retrievers.keywords_retriever import KeywordRetriever


class SchemaRetriever:
    """
    Coordinates all schema retrieval strategies.
    """

    def __init__(self):

        self.retrievers = [
            KeywordRetriever(),
        ]

    def retrieve(
        self,
        schema: dict,
        question: str,
        documents: list[SchemaDocument],
    ) -> dict:
        """
        Execute all retrieval strategies and merge the results.
        """

        results = []

        for retriever in self.retrievers:

            results.append(

                retriever.retrieve(
                    schema=schema,
                    question=question,
                    documents=documents,
                )

            )

        merged = self._merge_results(results)

        return merged.schema

    def _merge_results(
        self,
        results: list[RetrievalResult],
    ) -> RetrievalResult:
        """
        Merge retrieval results.

        Currently returns the keyword retrieval.

        Later this will perform score fusion.
        """

        return results[0]