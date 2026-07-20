from dataclasses import dataclass

@dataclass
class RetrievalResult:
    """
    Represents the result of a retrieval operation.
    """
    schema: dict
    scores: dict[str, float]