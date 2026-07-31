import re

from sqlglot import column 

class SchemaCompressor :
    """
    removes irrlevant schema information before sending it to the LLM 
    
    """
    
    def compress(self, schema: dict, question: str) -> dict:
        
        raise NotImplementedError("Subclasses must implement the compress method.")
    
    def _tokenize(self, question: str) -> set[str]:
        """
        Tokenizes the question into a list of lowercase words.
        """
        return set(re.findall(
            r"\w+",
            question.lower(),
        ))
    
    def _keep_column(self, column_name: str, tokens: set[str]) -> bool:
        """
        Determines whether to keep a column based on its name and the question tokens.
        """
        name = column["name"].lower()
        if name in tokens:
            return True
        return False
    
    def _compress_table(self, table: dict, tokens: set[str]) -> dict:
        
        columns = [
            column
            for column in table["columns"]
            if self._keep_column(column["name"], tokens)
        ]
        
        return {
            "columns": columns,
            "primary_keys": table["primary_keys"],
            "foreign_keys": table["foreign_keys"],
        }
        
    def compress(self, schema: dict, question: str) -> dict:
        
        tokens = self._tokenize(question)
        
        compressed = {}
        
        for table_name, table in schema.items():
            
            compressed[table_name] = self._compress_table(table, tokens)
            
        return compressed

