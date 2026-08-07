from dataclasses import dataclass, field


@dataclass
class SchemaDocument:
    """
    Represents one searchable schema document.
    """

    id: str

    table_name: str

    content: str

    metadata: dict = field(default_factory=dict)

    score: float = 0.0