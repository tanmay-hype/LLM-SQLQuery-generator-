import re 
from collections import defaultdict

class SchemaRetriever:
    """
    Retrieves the most relevant tables from the schema
    based on a natural language question.
    """
    TABLE_EXACT_MATCH = 10
    TABLE_PARTIAL_MATCH = 5
    COLUMN_EXACT_MATCH = 6
    COLUMN_PARTIAL_MATCH = 3
    
    def retrieve(self, schema: dict, question: str, top_k: int = 5) -> dict:
        """
        Retrieve the most relevant tables from the schema based on the question.
        """
        tokens = self._tokenize(question)
        scores = self._score_tables(schema, tokens)
        return self._select_tables(schema, scores, top_k)
    
    def _tokenize(self, question: str) -> list[str]:
        """
        Tokenize the question into searchable tokens.
        """
        tokens = re.findall(r'\w+', question.lower())
        return tokens
    
    def _score_tables(self, schema: dict, tokens: list[str]) -> dict:
        """
        Score each table based on the number of matching tokens.
        """
        scores = {}
        for table_name, table_info in schema.items():
            score = 0 
            score += self._table_score(table_name, tokens)
            score += self._column_score(table_info.get("columns", []), tokens)
            if score > 0:
                scores[table_name] = score

        return scores
    
    def _select_tables(self, schema: dict, scores: dict, top_k: int) -> dict:
        """
        Select the top_k tables based on their scores.
        """
        if not scores:
            return dict(list(schema.items())[:top_k])  # Return first top_k tables if no scores 
        ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        selected = {}
        for table_name, _ in ranked[:top_k]:
            selected[table_name] = schema[table_name]
        return selected
    
    def _table_score(self, table_name: str, tokens: list[str]) -> int:
        """
        Calculate the score for a single table based on token matches.
        """
        score = 0
        table = table_name.lower()
        for token in tokens:
            if token == table:
                score += self.TABLE_EXACT_MATCH
            elif token in table:
                score += self.TABLE_PARTIAL_MATCH
        return score
    
    def _column_score(self, columns: list[str], tokens: list[str]) -> int:
        """
        Calculate the score for a single column based on token matches.
        """
        score = 0
        for column in columns:
            column_name = column["name"].lower()
            for token in tokens:
                if token == column_name:
                    score += self.COLUMN_EXACT_MATCH
                elif token in column_name:
                    score += self.COLUMN_PARTIAL_MATCH
        return score