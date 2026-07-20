import re

from sqlalchemy import table

from app.core.config import settings
from app.schema.retrievers.base import BaseSchemaRetriever
from app.schema.models.retrieval_result import RetrievalResult

class KeywordRetriever(BaseSchemaRetriever):
    """
    Retrieves the most relevant tables from the schema
    using keyword matching.
    """

    TABLE_EXACT_MATCH = 10
    TABLE_PARTIAL_MATCH = 5

    COLUMN_EXACT_MATCH = 6
    COLUMN_PARTIAL_MATCH = 3

    def retrieve(
        self,
        schema: dict,
        question: str,
        top_k: int = settings.schema_retriever_top_k,
    ) -> RetrievalResult:
        """
        Retrieve the most relevant tables from the schema.
        """

        tokens = self._tokenize(question)

        scores = self._score_tables(
            schema,
            tokens,
        )

        selected_schema = self._select_tables(
            schema,
            scores,
            top_k,
        )
       
        selected_tables = self._expand_related_tables(
            schema,
            set(selected_schema.keys()),
        )
        
        final_schema = {
            table: schema[table]
            for table in selected_tables
        }


        return RetrievalResult(
            schema=selected_schema,
            scores=scores
        )

    def _tokenize(
        self,
        question: str,
    ) -> list[str]:

        return re.findall(
            r"\w+",
            question.lower(),
        )

    def _score_tables(
        self,
        schema: dict,
        tokens: list[str],
    ) -> dict:

        scores = {}

        for table_name, table_info in schema.items():

            score = 0

            score += self._table_score(
                table_name,
                tokens,
            )

            score += self._column_score(
                table_info.get("columns", []),
                tokens,
            )

            if score > 0:
                scores[table_name] = score

        return scores

    def _select_tables(
        self,
        schema: dict,
        scores: dict,
        top_k: int,
    ) -> dict:

        filtered_scores = {
            table: score
            for table, score in scores.items()
            if score >= settings.schema_retriever_min_score
        }

        if not filtered_scores:
            return dict(
                list(schema.items())[:top_k]
            )

        ranked = sorted(
            filtered_scores.items(),
            key=lambda item: item[1],
            reverse=True,
        )

        selected = {}

        for table_name, _ in ranked[:top_k]:
            selected[table_name] = schema[table_name]

        return selected

    def _table_score(
        self,
        table_name: str,
        tokens: list[str],
    ) -> int:

        score = 0

        table_name = table_name.lower()

        for token in tokens:

            if token == table_name:
                score += self.TABLE_EXACT_MATCH

            elif token in table_name:
                score += self.TABLE_PARTIAL_MATCH

        return score

    def _column_score(
        self,
        columns: list[dict],
        tokens: list[str],
    ) -> int:

        score = 0

        for column in columns:

            column_name = column["name"].lower()

            for token in tokens:

                if token == column_name:
                    score += self.COLUMN_EXACT_MATCH

                elif token in column_name:
                    score += self.COLUMN_PARTIAL_MATCH

        return score

    def _expand_related_tables(
        self,
        schema: dict,
        selected_tables: set[str],
    ) -> set[str]:

        expanded = set(selected_tables)

        for table_name, table_info in schema.items():

            for fk in table_info.get("foreign_keys", []):

                referred = fk.get("referred_table")

                if table_name in selected_tables and referred:
                    expanded.add(referred)

                if referred in selected_tables:
                    expanded.add(table_name)

        return expanded