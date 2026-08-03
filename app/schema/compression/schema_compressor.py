import re
from app.models.intent_analysis import IntentAnalysis
from app.models.intent import QueryIntent

class SchemaCompressor :
    """
    removes irrlevant schema information before sending it to the LLM 
    
    """
    
    def compress(self, schema: dict, question: str, intent: IntentAnalysis) -> dict:
        
        raise NotImplementedError("Subclasses must implement the compress method.")
    
    def _tokenize(self, question: str) -> set[str]:
        """
        Tokenizes the question into a list of lowercase words.
        """
        return set(re.findall(
            r"\w+",
            question.lower(),
        ))
    
    def _keep_column(self, column: dict, table: dict, tokens: set[str], intent: IntentAnalysis) -> bool:
        """
        Determines whether to keep a column based on its name and the question tokens.
        """
        name = column["name"].lower()
        
        #Direct keyword match 
        if name in tokens:
            return True
        
        #Always preserve identifier columns
        if name.endswith("_id"):
            return True
        
        if name == "id":
            return True
        
        #preserve primary keys 
        pk = table.get("primary_keys", {})
        constrained = pk.get("constrained_columns", [])
        if name in constrained:
            return True
        
        #preserve foreign keys
        for fk in table.get("foreign_keys", []):
            if name in fk.get("constrained_columns", []):
                return True
            
        COMMON_COLUMNS = {
            "name",
            "title",
            "status",
            "type",
            "category",
            "amount",
            "price",
            "quantity",
            "date",
            "created_at",
            "updated_at",
        }
        if name in COMMON_COLUMNS:
            return True
        
        if not columns:
            columns = table["columns"][:3]
        
        if intent.primary == QueryIntent.TIME_SERIES:
            if "date" in name or "time" in name:
                return True
        
        if intent.primary == QueryIntent.AGGREGATION:
            if any(word in name for word in (
                "amount",
                "price",
                "cost",
                "total",
                "quantity",
                "count",
                "salary",
                "revenue",
                )
            ):
                return True      
            
        return False
    
    def _compress_table(self, table: dict, tokens: set[str], intent: IntentAnalysis) -> dict:
        
        columns = [
            column
            for column in table["columns"]
            if self._keep_column(column = column, table = table, tokens = tokens, intent = intent)
        ]
        
        return {
            "columns": columns,
            "primary_keys": table["primary_keys"],
            "foreign_keys": table["foreign_keys"],
        }
        
    def compress(self, schema: dict, question: str, intent: IntentAnalysis) -> dict:
        
        tokens = self._tokenize(question)
        
        compressed = {}
        
        for table_name, table in schema.items():
            
            compressed[table_name] = self._compress_table(table = table, tokens = tokens, intent = intent)
            
        return compressed

