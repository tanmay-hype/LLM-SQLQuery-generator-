from dataclasses import dataclass, field 

@dataclass 
class SchemaDocument:
    """
    Represents a schema document with its content and metadata.
    """
    table_name: str
    content: str
    metadata: dict = field(default_factory=dict)
    score: float = 0.0

 