from dataclasses import dataclass, field

from app.schema.models.schema_document import SchemaDocument

@dataclass
class RetrievalResult:
    """
    Represents the result of a retrieval operation.
    """
    schema: dict
    documents : list[SchemaDocument] = field(default_factory=list)
    scores: dict[str, float] = field(default_factory=dict)  