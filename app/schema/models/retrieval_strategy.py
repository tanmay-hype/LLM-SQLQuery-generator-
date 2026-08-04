from enum import Enum 

class RetrievalStrategy(str, Enum):
    """
    Enum representing different retrieval strategies for schema documents.
    """
    KEYWORD = "keyword"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"