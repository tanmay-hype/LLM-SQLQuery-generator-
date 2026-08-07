from dataclasses import dataclass
from app.schema.models.schema_document import SchemaDocument

@dataclass
class SemanticMatch:
    document: SchemaDocument
    score: float
