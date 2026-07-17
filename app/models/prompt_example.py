from dataclasses import dataclass
from app.models.intent import QueryIntent

@dataclass(frozen=True)
class PromptExample:
    """
    Represents a single prompt example for the LLM.
    """
    intents: set[QueryIntent]
    question: str
    sql: str
    